class Agyswap < Formula
  desc "Fast Multi-Account Switcher for Google Antigravity (agy) CLI on macOS"
  homepage "https://github.com/g1mn/agyswap"
  # NOTE: this url/sha256 still pins v0.4.0, which predates modules/quota.py and
  # modules/tui/ — bin.install "modules" below will only install the (older)
  # modules/ that actually exists in whatever tag is pinned here. Bump url/sha256
  # to a release that contains modules/quota.py + modules/tui/ before relying on
  # `agyswap quota`/`tui`/`watch` working via Homebrew.
  url "https://github.com/g1mn/agyswap/archive/refs/tags/v0.4.0.tar.gz"
  sha256 "c4306ad539fad88656b0f349ba35a30195a7e6d6affa671c12a6689c52a88d10"
  license "MIT"

  depends_on :macos

  def install
    if File.exist?("agyswap.py")
      bin.install "agyswap.py" => "agyswap"
    else
      bin.install "bin/agyswap" => "agyswap"
    end
    # modules/ (ctx, quota, tui) must sit next to the installed binary — agyswap.py
    # resolves its own real path (following the Homebrew symlink) to find it.
    bin.install "modules" if File.directory?("modules")
    generate_completions_from_executable(bin/"agyswap", "completion")
  end

  def caveats
    <<~EOS
      `agyswap tui` / `agyswap watch` need the `rich` and `textual` Python packages,
      which this formula does not vendor. Install them once with:
        pip3 install --user rich textual
      Everything else (list/switch/add/ctx/quota/...) works with no extra setup.
    EOS
  end

  test do
    assert_match "agyswap #{version}", shell_output("#{bin}/agyswap --version")
    assert_match "Security Audit", shell_output("#{bin}/agyswap audit")
    # Not asserting modules/quota.py exists here — it depends on which tag is
    # pinned above (see NOTE), so a hardcoded assertion would break `brew test`
    # for any pin that predates it.
  end
end
