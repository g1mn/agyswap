class Agyswap < Formula
  desc "Fast Multi-Account Switcher for Google Antigravity (agy) CLI on macOS"
  homepage "https://github.com/g1mn/agyswap"
  url "https://github.com/g1mn/agyswap/archive/refs/tags/v0.2.0.tar.gz"
  sha256 "b9fb560b4518d4681dccebd344d1edca3caae301c9d595b8912424fffe7d7f73"
  license "MIT"

  depends_on :macos

  def install
    if File.exist?("agyswap.py")
      bin.install "agyswap.py" => "agyswap"
    else
      bin.install "bin/agyswap" => "agyswap"
    end
    generate_completions_from_executable(bin/"agyswap", "completion")
  end

  test do
    assert_match "agyswap #{version}", shell_output("#{bin}/agyswap --version")
    assert_match "Security Audit", shell_output("#{bin}/agyswap audit")
  end
end
