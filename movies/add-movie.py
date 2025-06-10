import argparse
import os
import requests
import shutil
from pathlib import Path
import re

def sanitize_filename(title):
    """Sanitizes a string to be a safe filename."""
    # Replace spaces with hyphens
    filename = title.lower().replace(' ', '-')
    # Remove characters that are not alphanumeric, hyphens, or periods
    filename = re.sub(r'[^a-z0-9-.]', '', filename)
    return filename

def add_movie_to_html(
    html_file_path: str,
    image_source: str,
    title: str,
    year: str,
    description: str
):
    """
    Adds a new movie article to the movies.html file.

    Args:
        html_file_path: Path to the movies.html file.
        image_source: URL or local path to the movie poster image.
        title: Title of the movie.
        year: Year of the movie.
        description: Text description/themes of the movie.
    """
    assets_dir = Path("./assets")
    assets_dir.mkdir(parents=True, exist_ok=True) # Ensure assets directory exists

    image_filename = ""
    # Determine if image_source is a URL or a local path
    if image_source.startswith("http://") or image_source.startswith("https://"):
        try:
            response = requests.get(image_source, stream=True)
            response.raise_for_status() # Raise an exception for bad status codes

            # Determine file extension from URL or content type
            content_type = response.headers.get('Content-Type')
            if 'image/jpeg' in content_type:
                ext = '.jpg'
            elif 'image/png' in content_type:
                ext = '.png'
            elif 'image/gif' in content_type:
                ext = '.gif'
            else:
                # Fallback: try to guess from URL, or default to .jpg
                ext = Path(image_source).suffix or '.jpg'

            image_filename_base = sanitize_filename(f"{title}-{year}")
            image_filename = f"{image_filename_base}{ext}"
            image_path_in_assets = assets_dir / image_filename

            with open(image_path_in_assets, 'wb') as out_file:
                shutil.copyfileobj(response.raw, out_file)
            print(f"Downloaded image to {image_path_in_assets}")

        except requests.exceptions.RequestException as e:
            print(f"Error downloading image from URL {image_source}: {e}")
            return
    else:
        # Assume it's a local file path
        source_image_path = Path(image_source)
        if not source_image_path.is_file():
            print(f"Error: Local image file not found at {source_image_path}")
            return

        # Sanitize filename, keeping original extension
        image_filename_base = sanitize_filename(f"{title}-{year}")
        image_filename = f"{image_filename_base}{source_image_path.suffix}"
        image_path_in_assets = assets_dir / image_filename

        try:
            shutil.copy(source_image_path, image_path_in_assets)
            print(f"Copied image to {image_path_in_assets}")
        except IOError as e:
            print(f"Error copying image from {source_image_path}: {e}")
            return

    # Construct the new article HTML
    new_article_html = f"""
      <article class="movie">
        <img
          src="./assets/{image_filename}"
          alt="{title} ({year}) movie poster"
        />
        <div class="text-content">
          <h2>{title} ({year})</h2>
          <p>
            {description}
          </p>
        </div>
      </article>"""

    # Read the existing HTML file
    try:
        with open(html_file_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
    except FileNotFoundError:
        print(f"Error: HTML file not found at {html_file_path}")
        return
    except Exception as e:
        print(f"Error reading HTML file: {e}")
        return

    # Find the </main> tag and insert the new article before it
    insertion_point = html_content.rfind('</main>') # rfind for robustness
    if insertion_point == -1:
        print("Error: Could not find </main> tag in the HTML file. Aborting.")
        return

    modified_html_content = (
        html_content[:insertion_point] +
        new_article_html +
        html_content[insertion_point:]
    )

    # Write the modified content back to the HTML file
    try:
        with open(html_file_path, 'w', encoding='utf-8') as f:
            f.write(modified_html_content)
        print(f"Successfully added '{title} ({year})' to {html_file_path}")
    except Exception as e:
        print(f"Error writing to HTML file: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Add a new movie article to your movies.html page.",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument(
        "image_source",
        help="URL of the movie poster image (e.g., 'https://example.com/poster.jpg')\n"
             "OR local path to the image file (e.g., '~/Downloads/my_movie.png')"
    )
    parser.add_argument("title", help="Title of the movie (e.g., 'Parasite')")
    parser.add_argument("year", help="Year of the movie (e.g., '2019')")
    parser.add_argument("description", help="Short description/themes of the movie.")
    parser.add_argument(
        "--html_file",
        default="index.html",
        help="Path to your HTML file (default: index.html)"
    )

    args = parser.parse_args()

    add_movie_to_html(
        args.html_file,
        args.image_source,
        args.title,
        args.year,
        args.description
    )
