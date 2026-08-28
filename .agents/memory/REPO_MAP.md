# 🗺️ Compact Repository Map (8 files indexed)

📁 `agyswap.py` (1828 lines):
  def c(text, color_code)
  def bold(text)
  def green(text)
  def yellow(text)
  def blue(text)
  def cyan(text)
  def red(text)
  def gray(text)
  def magenta(text)
  def secure_opener(path, flags)
  def file_lock() # Acquires an exclusive file lock for concurrent process safety.
  class KeychainManager:
      @classmethod def get_raw_password(cls)
      @classmethod def get_current_payload(cls)
      @classmethod def set_payload(cls, payload)
  def token_fingerprint(token_str) # Returns SHA-256 fingerprint of token to identify matches locally without API calls.
  def extract_jwt_claims(token_str) # Parses offline claims from JWT tokens without network requests.
  def fetch_google_userinfo(access_token)
  class StorageManager:
      @classmethod def init_storage(cls)
      @classmethod def load_config(cls)
      @classmethod def save_config(cls, cfg)
      @classmethod def _find_latest_backup(cls)
      @classmethod def _backup_config(cls)
      @classmethod def load_slot(cls, slot_num)
      @classmethod def save_slot(cls, slot_num, data)
      @classmethod def remove_slot_file(cls, slot_num)
  def parse_iso_datetime(iso_str) # Parses ISO-8601 strings (including 'Z' suffix) into UTC-aware datetime objects.
  def format_expiry_detail(exp_str) # Formats token expiration time:
  def time_ago_str(iso_str) # Converts ISO timestamp into relative '~ ago' string.
  def find_account(accounts, target) # Finds account entry by slot number, email, or alias (case-insensitive).
  def get_running_instances() # Detects active running agy CLI sessions using a single lsof call.
  def warn_running_instances() # Prints warning if active agy sessions are detected.
  def cmd_list(args) # Displays accounts list with tree-style token expiry view.
  def cmd_status(args) # Displays active Keychain token and account state.
  def cmd_add(args) # Registers current Keychain session as a new slot or updates an existing one.
  def cmd_switch(args) # Switches active Antigravity profile to target slot number or email/alias.
  def cmd_remove(args) # Deletes target slot.
  def cmd_rename(args) # Renames an account slot alias.
  def cmd_whoami(args) # Fetches real-time profile from Google UserInfo API.
  def cmd_sync(args) # Syncs latest Keychain credentials back to slot storage.
  def _get_oauth_client_info() # Synthesizes Google OAuth credentials at runtime to avoid scanner false positives.
  def refresh_oauth_token(refresh_token) # Directly requests a fresh OAuth access token from Google using stored refresh_token.
  def rotate_single_slot(slot_num, is_active) # Refreshes token for a single slot and syncs to Keychain if active.
  def cmd_rotate(args) # Refreshes expired OAuth credentials using stored refresh token in background.
  def cmd_health(args) # Overview dashboard of token expiry status across all slots.
  def cmd_audit(args) # Audits and auto-corrects filesystem permissions and Keychain integrity.
  def cmd_export(args) # Exports slot metadata to JSON format (tokens excluded for security).
  def cmd_import(args) # Imports slot metadata from JSON file with automatic slot number conflict resolution.
  def safe_json_for_script(data) # Safely escapes JSON data to prevent Stored XSS inside HTML <script> tags.
  def cmd_viz(args) # Generates an interactive HTML dashboard in isolated ~/.agy-swap/ without modifying git-tracked docs/.
  def cmd_completion(args) # Generates shell auto-completion scripts.
  def cmd_context(args) # Handles 'agyswap context' (or 'agyswap ctx') subcommands.
  def main()
📁 `install.sh` (72 lines)
📁 `test_context.py` (64 lines):
  class TestContextModule(unittest.TestCase):
      def test_token_budgeter_boundaries()
      def test_repomap_python_ast_and_decorators()
      def test_repomap_generic_fallback()
      def test_state_manager_save_and_permissions()
📁 `modules/__init__.py` (3 lines)
📁 `modules/context/__init__.py` (8 lines)
📁 `modules/context/budgeter.py` (36 lines):
  class TokenBudgeter:
      @staticmethod def estimate_tokens(text)
      @classmethod def trim_to_budget(cls, text, max_tokens)
📁 `modules/context/repomap.py` (176 lines):
  class RepoMapper:
      def __init__(root_dir, max_tokens)
      def generate_map()
      def _parse_file(full_path, rel_path)
      def _parse_python(content)
      def _parse_generic(content, ext)
📁 `modules/context/state.py` (112 lines):
  class StateManager:
      def __init__(root_dir)
      def get_git_status()
      def snapshot(goal)
      def save_snapshot(goal)