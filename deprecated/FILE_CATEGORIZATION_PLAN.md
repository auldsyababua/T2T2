# Repository Cleanup Plan

## PRODUCTION FILES (Keep in root)
- t2t2_chat_indexer.py - Main bot for users
- t2t2_qr_auth.py - Railway QR auth server
- supabase_client_wrapper.py - Shared database utility
- telethon_crawler.py - Data collection utility

## OLD BOTS (Move to deprecated/old_bots/)
- bot.py - Old version
- bot_old.py - Even older version
- simple_bot.py - Simplified version
- multi_user_bot.py - Multi-user attempt
- optimized_t2t2_bot.py - Performance attempt
- supabase_team_bot.py - Team features attempt
- t2t2_auth_bot.py - Separate auth bot
- t2t2_web_auth.py - Web auth attempt

## TEST SCRIPTS (Move to deprecated/test_scripts/)
- test_admin_auth_setup.py
- test_basic_bot.py
- test_bot_quick.py
- test_bot_simple.py
- test_chat_indexer.py
- test_direct_supabase_http.py
- test_qr_server_local.py
- test_s3_direct.py
- test_s3_wrapper.py
- test_simple_supabase.py
- test_supabase_connection_detailed.py
- test_supabase_connection.py
- test_telethon_auth.py

## MIGRATION/SETUP TOOLS (Move to deprecated/migration_tools/)
- admin_auth_tool.py - Admin authentication helper
- check_bot_setup.py - Setup validator
- debug_bot.py - Debugging utility
- execute_sql_supabase.py - Database migrations
- fix_bot_updates.py - Update fixer
- fix_supabase_key.py - Key migration
- quick_setup_bot.py - Quick setup
- troubleshoot_aws.py - AWS debugging
- use_jwt_service_role.py - JWT migration
- validate_aws_creds.py - AWS validation
- verify_supabase_key.py - Key verification