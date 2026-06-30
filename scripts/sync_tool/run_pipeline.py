import os
import subprocess
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from scripts.sync_tool.importer import process_imports

def main():
    missing_file = 'missing_articles.txt'
    if not os.path.exists(missing_file):
        print("No missing_articles.txt found.")
        return

    print("Starting automated import...")
    imported, failed = process_imports(missing_file)
    
    # Write reports
    with open('imported_articles.txt', 'w') as f:
        for url in imported:
            f.write(f"{url}\n")
            
    with open('failed_imports.txt', 'w') as f:
        for url, error in failed:
            f.write(f"{url}: {error}\n")
            
    # Summary
    print(f"\nImport Summary:")
    print(f"Total processed: {len(imported) + len(failed)}")
    print(f"Successfully imported: {len(imported)}")
    print(f"Failed: {len(failed)}")
    
    if imported:
        print("\nVerifying build...")
        try:
            # Build website using pelican directly
            subprocess.run(['pelican', 'content', '-o', 'output', '-s', 'pelicanconf.py'], check=True)
            print("Build successful.")
            
            # Git operations
            subprocess.run(['git', 'add', 'content/'], check=True)
            subprocess.run(['git', 'commit', '-m', 'Auto-import missing articles'], check=True)
            subprocess.run(['git', 'push'], check=True)
            print("Changes committed and pushed.")
        except subprocess.CalledProcessError as e:
            print(f"Build or Git operations failed: {e}")

if __name__ == "__main__":
    main()
