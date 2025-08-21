import logging
import time
import random
from typing import List, Dict
from urllib.parse import urljoin, urlparse, parse_qs
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
import undetected_chromedriver as uc
from scraper_utils import ScraperUtils

logger = logging.getLogger(__name__)

class GoogleCareersParser:
    def __init__(self):
        self.name = "Google Careers"
        self.base_url = "https://www.google.com"
        self.scraper_utils = ScraperUtils()
    
    def parse(self, url: str, keywords: List[str], selector: str = '') -> List[Dict]:
        """Parse Google Careers page for job listings"""
        jobs = []
        driver = None
        
        try:
            # Setup Chrome with anti-detection
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
            
            # Create driver
            driver = uc.Chrome(options=chrome_options)
            
            # Set random user agent and stealth scripts
            user_agent = self.scraper_utils.get_random_user_agent()
            driver.execute_cdp_cmd('Network.setUserAgentOverride', {"userAgent": user_agent})
            driver.execute_script(self.scraper_utils.get_stealth_script())
            
            # Add cache busting to URL
            cache_buster = self.scraper_utils.get_cache_buster()
            separator = '&' if '?' in url else '?'
            url_with_cache_buster = f"{url}{separator}{cache_buster}"
            
            logger.info(f"Loading Google Careers page: {url_with_cache_buster}")
            driver.get(url_with_cache_buster)
            
            # Wait for initial page load
            WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Random delay to mimic human behavior
            time.sleep(random.uniform(3, 6))
            
            # Wait for job listings to load - try multiple possible selectors
            job_selectors = [
                '[data-job-id]',
                '.job-result',
                '.job-listing',
                '[role="listitem"]',
                'li[data-job-id]',
                '[class*="job"]'
            ]
            
            job_elements = []
            for selector in job_selectors:
                try:
                    WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                    )
                    job_elements = driver.find_elements(By.CSS_SELECTOR, selector)
                    if job_elements:
                        logger.info(f"Found {len(job_elements)} job elements using selector: {selector}")
                        break
                except TimeoutException:
                    continue
            
            if not job_elements:
                # Fallback: look for any elements that might contain job information
                possible_selectors = [
                    'li',
                    '[role="button"]',
                    '.result',
                    '[class*="item"]'
                ]
                
                for selector in possible_selectors:
                    try:
                        elements = driver.find_elements(By.CSS_SELECTOR, selector)
                        # Filter elements that might be job listings
                        job_elements = [el for el in elements if self._is_likely_job_element(el)]
                        if job_elements:
                            logger.info(f"Found {len(job_elements)} potential job elements using fallback selector: {selector}")
                            break
                    except:
                        continue
            
            # Scroll to load more jobs if needed
            if job_elements:
                self._scroll_to_load_more(driver)
                
                # Re-fetch elements after scrolling
                for selector in job_selectors:
                    try:
                        new_elements = driver.find_elements(By.CSS_SELECTOR, selector)
                        if len(new_elements) > len(job_elements):
                            job_elements = new_elements
                            logger.info(f"Found {len(job_elements)} job elements after scrolling")
                            break
                    except:
                        continue
            
            # Parse job elements
            for element in job_elements:
                try:
                    job = self._extract_google_job_data(element, url)
                    if job and self._matches_keywords(job, keywords):
                        jobs.append(job)
                except Exception as e:
                    logger.warning(f"Error extracting job data from element: {e}")
                    continue
            
            logger.info(f"Successfully parsed {len(jobs)} matching jobs from Google Careers")
            
        except Exception as e:
            logger.error(f"Error parsing Google Careers page: {e}")
            raise
            
        finally:
            if driver:
                driver.quit()
        
        return jobs
    
    def _is_likely_job_element(self, element) -> bool:
        """Check if element is likely a job listing"""
        try:
            text = element.text.lower()
            # Look for job-related keywords in the element
            job_indicators = [
                'intern', 'engineer', 'developer', 'analyst', 'manager',
                'specialist', 'coordinator', 'associate', 'apprentice',
                'software', 'technical', 'product', 'data', 'research'
            ]
            
            # Check if element has meaningful text length and job keywords
            if len(text) > 20 and any(indicator in text for indicator in job_indicators):
                return True
            
            # Check for job-related attributes
            class_names = element.get_attribute('class') or ''
            if any(term in class_names.lower() for term in ['job', 'position', 'role', 'opening']):
                return True
                
            return False
        except:
            return False
    
    def _scroll_to_load_more(self, driver):
        """Scroll page to load more jobs if they're loaded dynamically"""
        try:
            # Get initial page height
            last_height = driver.execute_script("return document.body.scrollHeight")
            
            # Scroll in increments
            for i in range(3):  # Limit scrolling attempts
                # Scroll down
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                
                # Wait for new content to load
                time.sleep(random.uniform(2, 4))
                
                # Check if new content loaded
                new_height = driver.execute_script("return document.body.scrollHeight")
                if new_height == last_height:
                    break
                last_height = new_height
                
                logger.info(f"Scrolled page, new height: {new_height}")
                
        except Exception as e:
            logger.warning(f"Error while scrolling: {e}")
    
    def _extract_google_job_data(self, element, base_url: str) -> Dict:
        """Extract job data from a Google Careers job element"""
        try:
            job_data = {}
            
            # Try to get the job title
            title_selectors = [
                'h1', 'h2', 'h3', 'h4',
                '[class*="title"]',
                '[class*="heading"]',
                '[role="heading"]',
                'span[data-tooltip]',
                '.job-title'
            ]
            
            title = None
            for selector in title_selectors:
                try:
                    title_element = element.find_element(By.CSS_SELECTOR, selector)
                    if title_element:
                        title = title_element.text.strip()
                        if title and len(title) > 5:  # Ensure meaningful title
                            break
                except:
                    continue
            
            if not title:
                # Fallback: use element text (first line)
                element_text = element.text.strip()
                if element_text:
                    title = element_text.split('\n')[0][:100]
            
            # Try to get the job URL
            url = None
            try:
                link_element = element.find_element(By.TAG_NAME, 'a')
                if link_element:
                    href = link_element.get_attribute('href')
                    if href:
                        url = urljoin(base_url, href)
            except:
                pass
            
            # Try to get location
            location_selectors = [
                '[class*="location"]',
                '[class*="city"]',
                '[class*="office"]',
                'span:contains("CA")',
                'span:contains("NY")',
                'span:contains("WA")'
            ]
            
            location = None
            for selector in location_selectors:
                try:
                    location_element = element.find_element(By.CSS_SELECTOR, selector)
                    if location_element:
                        location = location_element.text.strip()
                        if location:
                            break
                except:
                    continue
            
            # Company is Google
            company = "Google"
            
            # Extract description from full element text
            description = element.text.strip()[:500]  # Limit description length
            
            # Clean up the data
            if title:
                job_data = {
                    'title': title,
                    'url': url,
                    'company': company,
                    'location': location,
                    'description': description
                }
                
                logger.debug(f"Extracted job: {title} at {location}")
                return job_data
            
        except Exception as e:
            logger.warning(f"Error extracting Google job data: {e}")
        
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
        for keyword in keywords:
            if keyword.lower() in text_to_search:
                return True
        
        return False
    
    def get_job_count(self, url: str) -> int:
        """Get total number of jobs available (if possible)"""
        # This could be implemented to extract total job count from the page
        # For now, return -1 to indicate unknown
        return -1
    
    def supports_pagination(self) -> bool:
        """Whether this parser supports pagination"""
        return True
    
    def get_next_page_url(self, current_url: str, soup: BeautifulSoup) -> str:
        """Get URL for next page if pagination exists"""
        # Google Careers typically uses infinite scroll, not pagination
        return None
