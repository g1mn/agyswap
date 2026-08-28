class Agyswap < Formula
  desc "Fast Multi-Account Switcher for Google Antigravity (agy) CLI on macOS"
  homepage "https://github.com/g1mn/agyswap"
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
    generate_completions_from_executable(bin/"agyswap", "completion")
  end

  test do
    assert_match "agyswap #{version}", shell_output("#{bin}/agyswap --version")
    assert_match "Security Audit", shell_output("#{bin}/agyswap audit")
  end
end
