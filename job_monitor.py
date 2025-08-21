import threading
import time
import requests
import hashlib
import logging
from typing import Dict, List, Optional
from datetime import datetime
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from fake_useragent import UserAgent
import undetected_chromedriver as uc
import random
import json
from urllib.parse import urljoin, urlparse
from scraper_utils import ScraperUtils
from parsers.google_careers_parser import GoogleCareersParser

logger = logging.getLogger(__name__)

class JobMonitor:
    def __init__(self, database, socketio):
        self.db = database
        self.socketio = socketio
        self.active_monitors = {}
        self.scraper_utils = ScraperUtils()
        
        # Initialize parsers
        self.parsers = {
            'google_careers': GoogleCareersParser(),
        }
    
    def start_monitor(self, monitor_id: int):
        """Start monitoring a specific job monitor"""
        monitor = self.db.get_monitor(monitor_id)
        if not monitor:
            logger.error(f"Monitor {monitor_id} not found")
            return
        
        if monitor_id in self.active_monitors:
            logger.info(f"Monitor {monitor_id} is already running")
            return
        
        # Create and start monitor thread
        stop_event = threading.Event()
        monitor_thread = threading.Thread(
            target=self._monitor_loop,
            args=(monitor, stop_event),
            daemon=True
        )
        
        self.active_monitors[monitor_id] = {
            'thread': monitor_thread,
            'stop_event': stop_event,
            'monitor': monitor
        }
        
        monitor_thread.start()
        logger.info(f"Started monitor {monitor_id}: {monitor['name']}")
        
        # Emit status update
        self.socketio.emit('monitor_status', {
            'monitor_id': monitor_id,
            'status': 'started',
            'message': f"Monitor '{monitor['name']}' started"
        })
    
    def stop_monitor(self, monitor_id: int):
        """Stop monitoring a specific job monitor"""
        if monitor_id not in self.active_monitors:
            logger.info(f"Monitor {monitor_id} is not running")
            return
        
        # Signal stop and wait for thread to finish
        self.active_monitors[monitor_id]['stop_event'].set()
        self.active_monitors[monitor_id]['thread'].join(timeout=5)
        
        # Remove from active monitors
        del self.active_monitors[monitor_id]
        
        logger.info(f"Stopped monitor {monitor_id}")
        
        # Emit status update
        self.socketio.emit('monitor_status', {
            'monitor_id': monitor_id,
            'status': 'stopped',
            'message': f"Monitor stopped"
        })
    
    def restart_monitor(self, monitor_id: int):
        """Restart a monitor"""
        self.stop_monitor(monitor_id)
        time.sleep(1)  # Brief pause
        self.start_monitor(monitor_id)
    
    def start_all_active_monitors(self):
        """Start all active monitors"""
        active_monitors = self.db.get_active_monitors()
        for monitor in active_monitors:
            self.start_monitor(monitor['id'])
    
    def test_monitor(self, monitor_id: int) -> Dict:
        """Test a monitor configuration"""
        monitor = self.db.get_monitor(monitor_id)
        if not monitor:
            raise Exception(f"Monitor {monitor_id} not found")
        
        try:
            # Run a single scrape
            results = self._scrape_jobs(monitor, test_mode=True)
            
            return {
                'success': True,
                'jobs_found': len(results['jobs']),
                'jobs': results['jobs'][:5],  # Return first 5 for preview
                'scrape_time': results['scrape_time'],
                'method': results['method']
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _monitor_loop(self, monitor: Dict, stop_event: threading.Event):
        """Main monitoring loop for a single monitor"""
        monitor_id = monitor['id']
        check_interval = monitor['check_interval']
        
        logger.info(f"Starting monitor loop for {monitor['name']} (ID: {monitor_id})")
        
        while not stop_event.is_set():
            try:
                # Scrape jobs
                start_time = time.time()
                results = self._scrape_jobs(monitor)
                scrape_time = time.time() - start_time
                
                jobs_found = len(results['jobs'])
                new_jobs = 0
                
                # Process and save new jobs
                for job in results['jobs']:
                    # Create content hash for deduplication
                    content_hash = self._create_content_hash(job)
                    
                    # Check if job already exists
                    if not self.db.job_exists(content_hash):
                        job_id = self.db.save_job(
                            monitor_id=monitor_id,
                            title=job.get('title', ''),
                            url=job.get('url', ''),
                            company=job.get('company', ''),
                            location=job.get('location', ''),
                            description=job.get('description', ''),
                            content_hash=content_hash
                        )
                        
                        if job_id:
                            new_jobs += 1
                            # Emit new job notification
                            self.socketio.emit('new_job', {
                                'monitor_id': monitor_id,
                                'monitor_name': monitor['name'],
                                'job': job,
                                'timestamp': datetime.now().isoformat()
                            })
                            
                            logger.info(f"New job found for monitor {monitor_id}: {job.get('title', 'Unknown')}")
                
                # Record monitor run
                self.db.record_monitor_run(
                    monitor_id=monitor_id,
                    jobs_found=jobs_found,
                    new_jobs=new_jobs,
                    success=True
                )
                
                # Emit status update
                self.socketio.emit('monitor_update', {
                    'monitor_id': monitor_id,
                    'jobs_found': jobs_found,
                    'new_jobs': new_jobs,
                    'scrape_time': round(scrape_time, 2),
                    'timestamp': datetime.now().isoformat(),
                    'method': results['method']
                })
                
                logger.info(f"Monitor {monitor_id} completed: {jobs_found} jobs found, {new_jobs} new")
                
            except Exception as e:
                logger.error(f"Error in monitor {monitor_id}: {e}")
                
                # Record failed run
                self.db.record_monitor_run(
                    monitor_id=monitor_id,
                    jobs_found=0,
                    new_jobs=0,
                    success=False,
                    error_message=str(e)
                )
                
                # Emit error
                self.socketio.emit('monitor_error', {
                    'monitor_id': monitor_id,
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                })
            
            # Wait for next check (or until stopped)
            stop_event.wait(check_interval)
        
        logger.info(f"Monitor loop stopped for {monitor['name']} (ID: {monitor_id})")
    
    def _scrape_jobs(self, monitor: Dict, test_mode: bool = False) -> Dict:
        """Scrape jobs from a monitor's URL"""
        url = monitor['url']
        keywords = monitor['keywords']
        
        # Determine which parser to use
        parser = self._get_parser(url)
        
        if parser:
            # Use specialized parser
            jobs = parser.parse(url, keywords, monitor.get('selector', ''))
            method = parser.name
        else:
            # Use generic scraping
            jobs = self._generic_scrape(url, keywords, monitor.get('selector', ''))
            method = 'generic'
        
        return {
            'jobs': jobs,
            'scrape_time': time.time(),
            'method': method
        }
    
    def _get_parser(self, url: str):
        """Get appropriate parser for URL"""
        domain = urlparse(url).netloc.lower()
        
        if 'google.com' in domain and 'careers' in url:
            return self.parsers.get('google_careers')
        
        return None
    
    def _generic_scrape(self, url: str, keywords: List[str], selector: str = '') -> List[Dict]:
        """Generic web scraping with fallback methods"""
        jobs = []
        
        # Try requests first (faster)
        try:
            jobs = self._scrape_with_requests(url, keywords, selector)
            if jobs:
                return jobs
        except Exception as e:
            logger.warning(f"Requests scraping failed for {url}: {e}")
        
        # Fallback to Selenium
        try:
            jobs = self._scrape_with_selenium(url, keywords, selector)
        except Exception as e:
            logger.error(f"Selenium scraping failed for {url}: {e}")
        
        return jobs
    
    def _scrape_with_requests(self, url: str, keywords: List[str], selector: str = '') -> List[Dict]:
        """Scrape using requests and BeautifulSoup"""
        headers = self.scraper_utils.get_random_headers()
        
        # Add cache-busting parameters
        cache_buster = self.scraper_utils.get_cache_buster()
        separator = '&' if '?' in url else '?'
        url_with_cache_buster = f"{url}{separator}{cache_buster}"
        
        response = requests.get(url_with_cache_buster, headers=headers, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        return self._extract_jobs_from_soup(soup, url, keywords, selector)
    
    def _scrape_with_selenium(self, url: str, keywords: List[str], selector: str = '') -> List[Dict]:
        """Scrape using Selenium with anti-detection"""
        driver = None
        try:
            # Setup Chrome options with anti-detection
            chrome_options = Options()
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            # Random window size
            width, height = self.scraper_utils.get_random_window_size()
            chrome_options.add_argument(f'--window-size={width},{height}')
            
            # Create driver with undetected-chromedriver
            driver = uc.Chrome(options=chrome_options)
            
            # Set random user agent
            user_agent = self.scraper_utils.get_random_user_agent()
            driver.execute_cdp_cmd('Network.setUserAgentOverride', {"userAgent": user_agent})
            
            # Add cache-busting and navigate
            cache_buster = self.scraper_utils.get_cache_buster()
            separator = '&' if '?' in url else '?'
            url_with_cache_buster = f"{url}{separator}{cache_buster}"
            
            driver.get(url_with_cache_buster)
            
            # Random delay to mimic human behavior
            time.sleep(random.uniform(2, 5))
            
            # Wait for content to load
            WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Additional wait for dynamic content
            time.sleep(random.uniform(3, 7))
            
            # Parse the page
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            
            return self._extract_jobs_from_soup(soup, url, keywords, selector)
            
        finally:
            if driver:
                driver.quit()
    
    def _extract_jobs_from_soup(self, soup: BeautifulSoup, base_url: str, 
                               keywords: List[str], selector: str = '') -> List[Dict]:
        """Extract jobs from BeautifulSoup object"""
        jobs = []
        
        # Use custom selector if provided, otherwise try common job listing selectors
        selectors_to_try = []
        if selector:
            selectors_to_try.append(selector)
        
        # Common job listing selectors
        selectors_to_try.extend([
            '[data-job-id]',
            '.job-listing',
            '.job-item',
            '.job-result',
            '.position',
            '.opening',
            '[class*="job"]',
            '[class*="position"]',
            '[class*="opening"]'
        ])
        
        # Try each selector
        for sel in selectors_to_try:
            try:
                job_elements = soup.select(sel)
                if job_elements:
                    for element in job_elements:
                        job = self._extract_job_data(element, base_url, keywords)
                        if job and self._matches_keywords(job, keywords):
                            jobs.append(job)
                    break  # Stop after finding matching elements
            except Exception as e:
                logger.warning(f"Error with selector '{sel}': {e}")
                continue
        
        return jobs
    
    def _extract_job_data(self, element, base_url: str, keywords: List[str]) -> Optional[Dict]:
        """Extract job data from a single job element"""
        try:
            # Extract title
            title_selectors = ['h1', 'h2', 'h3', '.title', '.job-title', '[class*="title"]']
            title = None
            for sel in title_selectors:
                title_elem = element.select_one(sel)
                if title_elem:
                    title = title_elem.get_text(strip=True)
                    break
            
            if not title:
                title = element.get_text(strip=True)[:100]  # Fallback
            
            # Extract URL
            url = None
            link_elem = element.find('a', href=True)
            if link_elem:
                url = urljoin(base_url, link_elem['href'])
            
            # Extract company
            company_selectors = ['.company', '.employer', '[class*="company"]', '[class*="employer"]']
            company = None
            for sel in company_selectors:
                company_elem = element.select_one(sel)
                if company_elem:
                    company = company_elem.get_text(strip=True)
                    break
            
            # Extract location
            location_selectors = ['.location', '.city', '[class*="location"]', '[class*="city"]']
            location = None
            for sel in location_selectors:
                location_elem = element.select_one(sel)
                if location_elem:
                    location = location_elem.get_text(strip=True)
                    break
            
            # Extract description
            description = element.get_text(strip=True)[:500]  # Limit description length
            
            return {
                'title': title,
                'url': url,
                'company': company,
                'location': location,
                'description': description
            }
            
        except Exception as e:
            logger.warning(f"Error extracting job data: {e}")
            return None
    
    def _matches_keywords(self, job: Dict, keywords: List[str]) -> bool:
        """Check if job matches any of the keywords"""
        if not keywords:
            return True
        
        # Combine all job text for searching
        text_to_search = ' '.join([
            job.get('title', ''),
            job.get('company', ''),
            job.get('location', ''),
            job.get('description', '')
        ]).lower()
        
        # Check if any keyword matches
        return any(keyword.lower() in text_to_search for keyword in keywords)
    
    def _create_content_hash(self, job: Dict) -> str:
        """Create a hash for job deduplication"""
        content = f"{job.get('title', '')}{job.get('company', '')}{job.get('url', '')}"
        return hashlib.md5(content.encode()).hexdigest()
