import os
import glob

def delete_png_files():
    """Delete all .png files in the current directory"""
    try:
        # Get all .png files in current directory
        png_files = glob.glob("*.png")
        
        if not png_files:
            print("No .png files found in the current directory.")
            return
        
        print(f"Found {len(png_files)} .png file(s):")
        for file in png_files:
            print(f"  - {file}")
        
        # Ask for confirmation
        confirm = input("\nDo you want to delete all these files? (y/N): ").lower().strip()
        
        if confirm == 'y' or confirm == 'yes':
            deleted_count = 0
            for file in png_files:
                try:
                    os.remove(file)
                    print(f"Deleted: {file}")
                    deleted_count += 1
                except OSError as e:
                    print(f"Error deleting {file}: {e}")
            
            print(f"\nSuccessfully deleted {deleted_count} out of {len(png_files)} .png files.")
        else:
            print("Operation cancelled.")
            
    except Exception as e:
        print(f"An error occurred: {e}")

def delete_png_files_silent():
    """Delete all .png files without confirmation (use with caution!)"""
    try:
        png_files = glob.glob("*.png")
        deleted_count = 0
        
        for file in png_files:
            try:
                os.remove(file)
                deleted_count += 1
            except OSError as e:
                print(f"Error deleting {file}: {e}")
        
        print(f"Deleted {deleted_count} .png files.")
        
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    # Use the safe version with confirmation by default
    delete_png_files()
    
    # Uncomment the line below if you want to delete without confirmation
    # delete_png_files_silent()
