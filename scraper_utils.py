import random
import time
import hashlib
from fake_useragent import UserAgent
from typing import Dict, Tuple

class ScraperUtils:
    def __init__(self):
        self.ua = UserAgent()
        
        # Common browser user agents for fallback
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15'
        ]
    
    def get_random_user_agent(self) -> str:
        """Get a random user agent string"""
        try:
            return self.ua.random
        except:
            return random.choice(self.user_agents)
    
    def get_random_headers(self) -> Dict[str, str]:
        """Get random headers to avoid detection"""
        headers = {
            'User-Agent': self.get_random_user_agent(),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': random.choice([
                'en-US,en;q=0.9',
                'en-GB,en;q=0.9',
                'en-CA,en;q=0.9,fr;q=0.8'
            ]),
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache'
        }
        
        # Randomly include additional headers
        if random.random() > 0.5:
            headers['Sec-CH-UA'] = '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"'
            headers['Sec-CH-UA-Mobile'] = '?0'
            headers['Sec-CH-UA-Platform'] = f'"{random.choice(["Windows", "macOS", "Linux"])}"'
        
        return headers
    
    def get_cache_buster(self) -> str:
        """Generate cache-busting parameters"""
        timestamp = str(int(time.time()))
        random_val = str(random.randint(10000, 99999))
        
        # Create a variety of cache-busting parameter names
        param_names = ['_t', 'cache', 'v', 'timestamp', 'cb', 'nocache', 'bust']
        param_name = random.choice(param_names)
        
        return f"{param_name}={timestamp}{random_val}"
    
    def get_random_window_size(self) -> Tuple[int, int]:
        """Get random window size to avoid detection"""
        # Common resolutions
        resolutions = [
            (1920, 1080),
            (1366, 768),
            (1440, 900),
            (1536, 864),
            (1280, 720),
            (1600, 900),
            (1024, 768),
            (1280, 1024)
        ]
        return random.choice(resolutions)
    
    def random_delay(self, min_seconds: float = 1.0, max_seconds: float = 3.0):
        """Add random delay to mimic human behavior"""
        delay = random.uniform(min_seconds, max_seconds)
        time.sleep(delay)
    
    def get_viewport_script(self) -> str:
        """Get JavaScript to set random viewport size"""
        width, height = self.get_random_window_size()
        return f"""
        Object.defineProperty(navigator, 'webdriver', {{
            get: () => undefined,
        }});
        
        window.outerWidth = {width};
        window.outerHeight = {height};
        window.innerWidth = {width - 20};
        window.innerHeight = {height - 100};
        """
    
    def get_stealth_script(self) -> str:
        """Get JavaScript to avoid detection"""
        return """
        // Remove webdriver property
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined,
        });
        
        // Mock chrome object
        window.chrome = {
            runtime: {},
        };
        
        // Mock permissions
        Object.defineProperty(navigator, 'permissions', {
            get: () => ({
                query: () => Promise.resolve({ state: 'granted' }),
            }),
        });
        
        // Mock plugins
        Object.defineProperty(navigator, 'plugins', {
            get: () => [1, 2, 3, 4, 5],
        });
        
        // Mock languages
        Object.defineProperty(navigator, 'languages', {
            get: () => ['en-US', 'en'],
        });
        """
    
    def should_use_proxy(self) -> bool:
        """Determine if proxy should be used (placeholder)"""
        # This can be expanded to implement proxy rotation
        return False
    
    def get_proxy_config(self) -> Dict:
        """Get proxy configuration (placeholder)"""
        # This can be expanded to implement proxy rotation
        return {}
    
    def create_session_fingerprint(self, url: str) -> str:
        """Create a unique fingerprint for this scraping session"""
        content = f"{url}{time.time()}{random.random()}"
        return hashlib.md5(content.encode()).hexdigest()[:8]
    
    def is_rate_limited(self, response_text: str) -> bool:
        """Check if response indicates rate limiting"""
        rate_limit_indicators = [
            'rate limit',
            'too many requests',
            'slow down',
            'temporarily blocked',
            'try again later',
            '429',
            'captcha',
            'robot'
        ]
        
        text_lower = response_text.lower()
        return any(indicator in text_lower for indicator in rate_limit_indicators)
    
    def extract_rate_limit_delay(self, headers: Dict) -> int:
        """Extract rate limit delay from response headers"""
        # Check common rate limit headers
        retry_after = headers.get('Retry-After')
        if retry_after:
            try:
                return int(retry_after)
            except:
                pass
        
        # Check X-RateLimit headers
        reset_time = headers.get('X-RateLimit-Reset')
        if reset_time:
            try:
                reset_timestamp = int(reset_time)
                current_time = int(time.time())
                return max(0, reset_timestamp - current_time)
            except:
                pass
        
        # Default delay if no specific time found
        return random.randint(60, 300)  # 1-5 minutes
