import asyncio
import os
from typing import Tuple

from noble_tls.utils.asset import generate_asset_name
from noble_tls.utils.asset import root_dir
from noble_tls.exceptions.exceptions import TLSClientException
import httpx

owner = 'depicts'
repo = 'tls-client'
url = f'https://api.github.com/repos/{owner}/{repo}/releases/latest'
root_directory = root_dir()


async def get_latest_release() -> Tuple[str, list]:
    """
    Fetches the latest release from the GitHub API.

    :return: Latest release tag name, and a list of assets
    """
    # Make a GET request to the GitHub API
    async with httpx.AsyncClient() as client:
        response = await client.get(url)

    # Check if the request was successful
    if response.status_code == 200:
        data = response.json()  # Parse the JSON data from the response
        version_num = data['tag_name'].replace('v', '')  # Return the tag name without the 'v' prefix
        if 'assets' not in data:
            raise TLSClientException(f"Version {version_num} does not have any assets.")

        # Get assets
        assets = data['assets']
        return version_num, assets
    else:
        raise TLSClientException(f"Failed to fetch the latest release. Status code: {response.status_code}")


async def download_and_save_asset(
        asset_url: str,
        asset_name: str,
        version: str
) -> None:
    # Download
    async with httpx.AsyncClient(follow_redirects=True) as client:
        headers = {
            'Accept': 'application/octet-stream',
            'User-Agent': 'noble-tls'
        }
        response = await client.get(asset_url, headers=headers)
        if response.status_code != 200:
            raise TLSClientException(f"Failed to download asset {asset_name}. Status code: {response.status_code}")

        with open(f'{root_directory}/dependencies/{asset_name}', 'wb') as f:
            f.write(response.content)

        # Save version info
        await save_version_info(asset_name, version)


async def save_version_info(asset_name: str, version: str):
    """
    Save version info to a hidden .version file in root_dir/dependencies
    """
    with open(f'{root_directory}/dependencies/.version', 'w') as f:
        f.write(f"{asset_name} {version}")


def read_version_info():
    """
    Read version info from a hidden .version file in root_dir/dependencies
    """
    try:
        with open(f'{root_directory}/dependencies/.version', 'r') as f:
            data = f.read()
            data = data.split(' ')
            return data[0], data[1]
    except FileNotFoundError:
        return None, None


async def download_if_necessary():    
    asset_name = generate_asset_name()
    version_num = "1.7.2"

    # Check if asset name is in the list of assets in root dir/dependencies
    if os.path.exists(f'{root_directory}/dependencies/{asset_name}'):
        return

    download_url = "https://chicken.nugget.wtf/tls-client-xgo-1.7.2-linux-amd64.so"
    await download_and_save_asset(download_url, asset_name, version_num)


async def update_if_necessary():
    await download_if_necessary()


if __name__ == "__main__":
    asyncio.run(update_if_necessary())
