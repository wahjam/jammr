-- Execute these SQL statements to permanently remove database tables belonging
-- to old apps that are no longer used with Python 3 and Django 1.11:
--
--   # docker exec -it postgres psql --user website
--
DROP TABLE easy_thumbnails_source CASCADE;
DROP TABLE easy_thumbnails_thumbnail CASCADE;
DROP TABLE filer_clipboard CASCADE;
DROP TABLE filer_clipboarditem CASCADE;
DROP TABLE filer_file CASCADE;
DROP TABLE filer_folder CASCADE;
DROP TABLE filer_folderpermission CASCADE;
DROP TABLE filer_image CASCADE;
DROP TABLE south_migrationhistory CASCADE;
DROP TABLE tagging_tag CASCADE;
DROP TABLE tagging_taggeditem CASCADE;
DROP TABLE zinnia_category CASCADE;
DROP TABLE zinnia_entry CASCADE;
DROP TABLE zinnia_entry_authors CASCADE;
DROP TABLE zinnia_entry_categories CASCADE;
DROP TABLE zinnia_entry_related CASCADE;
DROP TABLE zinnia_entry_sites CASCADE;
