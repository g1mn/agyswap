class Agyswap < Formula
  desc "Fast Multi-Account Switcher for Google Antigravity (agy) CLI on macOS"
  homepage "https://github.com/g1mn/agyswap"
  url "https://github.com/g1mn/agyswap/archive/refs/tags/v0.1.0.tar.gz"
  sha256 "b27b45721910967cf7d3103b4da52eaba1e9b2c4db64e26247c13eb45d36dcad"
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
