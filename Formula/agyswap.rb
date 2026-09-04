class Agyswap < Formula
  desc "Fast Multi-Account Switcher for Google Antigravity (agy) CLI on macOS"
  homepage "https://github.com/g1mn/agyswap"
  url "https://github.com/g1mn/agyswap/archive/refs/tags/v0.6.0.tar.gz"
  sha256 "7a82abb606929b541ca8e7b53194410228fbe0961c76ce686e86bab74df785b9"
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
    assert_predicate bin/"modules"/"quota.py", :exist?
  end
end
