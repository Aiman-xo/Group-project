def extract_s3_metadata(records):
    try:
        # This looks like this " file_key = company/company_infosys/admin/crawled_infosys.txt "
        file_key = records[0]["s3"]["object"]["key"]
        split_file = file_key.split('/')
        
        # Ensure the file path is deep enough to prevent IndexError
        if len(split_file) < 3:
            print(f"Skipping: Path too shallow -> {file_key}")
            return None

        company_plus_slug = split_file[1]
        folder_type = split_file[2]
        
        # Using maxsplit=1 handles company names that have underscores (e.g., company_tata_motors)
        slug_parts = company_plus_slug.split('_', 1)
        slug = slug_parts[1] if len(slug_parts) > 1 else company_plus_slug

        return {
            "slug": slug,
            "folder_type": folder_type,
            "file_key":file_key
        }
        
    except (KeyError, IndexError) as e:
        print(f"Error parsing S3 record: {e}")
        return None