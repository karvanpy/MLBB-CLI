import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Dict, Any
import requests
from requests import Session
import random
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

# Configure logging
logging.basicConfig(
    level=logging.ERROR,  # Change from INFO to ERROR to suppress most logs
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler('mlbb.log')]  # Redirect logs to file instead of terminal
)
logger = logging.getLogger(__name__)

# Add after logger initialization
console = Console()

@dataclass
class MLBBConfig:
    """Configuration class for MLBB API endpoints and headers."""
    SEND_VC_URL: str = "https://api.mobilelegends.com/base/sendVc"
    LOGIN_URL: str = "https://api.mobilelegends.com/base/login"
    GET_BASE_INFO_URL: str = "https://sg-api.mobilelegends.com/base/getBaseInfo"
    HEADERS: Dict[str, str] = None

    def __post_init__(self):
        self.HEADERS = {
            "Accept": "*/*",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Accept-Language": "en-US,en;q=0.9",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "Origin": "https://www.mobilelegends.com",
            "Referer": "https://www.mobilelegends.com/",
            "Sec-Ch-Ua": '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": '"Windows"',
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-site",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
        }

class MLBBLoginManager:
    """Manages MLBB login operations."""
    
    def __init__(self):
        self.session = requests.Session()
        self.config = MLBBConfig()
        
    def _make_request(self, url: str, payload: Dict[str, Any], headers: Optional[Dict] = None) -> Optional[Dict]:
        """Make HTTP request with error handling."""
        try:
            headers = headers or self.config.HEADERS
            response = self.session.post(url, headers=headers, data=payload)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Request failed: {str(e)}")
            return None

    def send_verification_code(self, role_id: str, zone_id: str) -> bool:
        """Send verification code request."""
        payload = {"roleId": role_id, "zoneId": zone_id}
        response = self._make_request(self.config.SEND_VC_URL, payload)
        
        if response:
            logger.info("Verification code sent! Please check your email.")
            logger.debug(f"Response: {response}")
            return True
        return False

    def login(self, role_id: str, zone_id: str, verification_code: str, referer: str) -> Optional[Dict]:
        """Perform login with verification code."""
        payload = {
            "roleId": role_id,
            "zoneId": zone_id,
            "vc": verification_code,
            "referer": referer,
            "type": "web"
        }
        
        response = self._make_request(self.config.LOGIN_URL, payload)
        if response:
            if response.get("code") == 0:
                logger.info("Login successful!")
                return response
            logger.error(f"Login failed: {response.get('message', 'Unknown error')}")
        return None

    def get_base_info(self, role_id: str, zone_id: str, jwt_token: str) -> Optional[Dict]:
        """Retrieve account base information."""
        payload = {"roleId": role_id, "zoneId": zone_id}
        headers = self.config.HEADERS.copy()
        headers["Authorization"] = f"Bearer {jwt_token}"
        
        response = self._make_request(self.config.GET_BASE_INFO_URL, payload, headers)
        if response:
            if response.get("code") == 0:
                self._display_account_info(response["data"])
                return response
            logger.error("Failed to get account info")
        return None
    def _display_account_info(self, data: Dict[str, Any]):
        """Display formatted account information."""
        info_table = Table(show_header=False, header_style="bold magenta")
        info_table.add_column("Field", style="cyan")
        info_table.add_column("Value", style="green")

        fields = [
            ("Avatar", data.get("avatar", "N/A")),
            ("Rank Level", data.get("historyRankLevel", "N/A")),
            ("Level", data.get("level", "N/A")),
            ("Name", data.get("name", "N/A")),
            ("Country", data.get("reg_country", "N/A")),
            ("Role ID", data.get("roleId", "N/A")),
            ("Zone ID", data.get("zoneId", "N/A"))
        ]

        for field, value in fields:
            info_table.add_row(field, str(value))

        console.print(Panel(
            info_table,
            title="[bold yellow]Account Information[/bold yellow]",
            border_style="blue"
        ))

def validate_input(prompt: str, validator=None) -> str:
    """Validate user input with optional validator function."""
    while True:
        try:
            value = console.input(f"[cyan]{prompt}[/cyan]").strip()
            if not value:
                console.print("[red]Input cannot be empty[/red]")
                continue
            if validator and not validator(value):
                console.print("[red]Invalid input format[/red]")
                continue
            return value
        except Exception as e:
            console.print(f"[red]Invalid input: {str(e)}[/red]")

def main():
    try:
        console.print("[bold blue]MLBB Account Login[/bold blue]", justify="center")
        console.print("=" * 50, justify="center")
        
        login_manager = MLBBLoginManager()
        
        # Get user inputs with validation
        role_id = validate_input("Enter your roleId: ", lambda x: x.isdigit())
        zone_id = validate_input("Enter your zoneId: ", lambda x: x.isdigit())
        
        # Generate random referer
        referer = f"{random.randint(2000000, 3000000)}_{random.randint(2000000, 3000000)}"
        
        # Send verification code with status indicator
        with console.status("[bold green]Sending verification code...[/bold green]"):
            if not login_manager.send_verification_code(role_id, zone_id):
                console.print("[bold red]Failed to send verification code[/bold red]")
                return
        
        # Get verification code from user
        verification_code = validate_input("Enter the verification code from your email: ")
        
        # Attempt login with status indicator
        with console.status("[bold green]Logging in...[/bold green]"):
            login_response = login_manager.login(role_id, zone_id, verification_code, referer)
            if not login_response:
                return
            
            # Get account info
            jwt_token = login_response["data"]["jwt"]
            account_info = login_manager.get_base_info(role_id, zone_id, jwt_token)
            
    except KeyboardInterrupt:
        console.print("\n[yellow]Operation cancelled by user[/yellow]")
    except Exception as e:
        console.print(f"[bold red]An unexpected error occurred: {str(e)}[/bold red]")

if __name__ == "__main__":
    main()