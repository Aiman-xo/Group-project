from app.core.logger import logger

def extract_s3_metadata(records):
    try:
        # This looks like this " file_key = company/company_infosys/admin/crawled_infosys.txt "
        # for competitor = file_key = company/company_infosys/competitor/competitor_slug/crawled_infosys.txt 
        file_key = records[0]["s3"]["object"]["key"]
        split_file = file_key.split('/')
        
        # Ensure the file path is deep enough to prevent IndexError
        if len(split_file) < 3:
            logger.warning(f"Skipping: Path too shallow -> {file_key}")
            return None

        company_plus_slug = split_file[1]
        folder_type = split_file[2]

        if folder_type == 'competitor':
            if len(split_file) < 4:
                logger.warning(f"Skipping: 'competitor' path missing slug segment -> {file_key}")
                return None
            competitor_slug_raw = split_file[3]
            competitor_slug = competitor_slug_raw.replace('_', '-')
        else:
            competitor_slug = None
        
        # Using maxsplit=1 handles company names that have underscores (e.g., company_tata_motors)
        slug_parts = company_plus_slug.split('_', 1)
        if len(slug_parts) < 2:
            logger.warning(f"Warning: '{company_plus_slug}' has no underscore, using as-is for slug -> {file_key}")
        slug_raw = slug_parts[1] if len(slug_parts) > 1 else company_plus_slug
        slug = slug_raw.replace('_', '-')

        return {
            "slug": slug,
            "folder_type": folder_type,
            "file_key":file_key,
            "competitor_slug":competitor_slug
        }
        
    except KeyError as e:
        logger.error(f"Error parsing S3 record: missing expected key {e} -> {records}")
        return None
    except IndexError as e:
        logger.error(f"Error parsing S3 record: unexpected path structure ({e}) -> {file_key if 'file_key' in locals() else records}")
        return None