class EsaTui < Formula
  include Language::Python::Virtualenv

  desc "TUI for Alibaba Cloud ESA management"
  homepage "https://github.com/delvinwang-inno/homebrew-esa-tui"
  url "https://github.com/delvinwang-inno/homebrew-esa-tui/archive/refs/tags/v0.1.0.tar.gz"
  sha256 "a3891b9e16e2fb0e76f0baf2596b6155e4a65a18a97f7a7c3205f0f0feb18d35"
  license "MIT"
  head "https://github.com/delvinwang-inno/homebrew-esa-tui.git", branch: "main"

  depends_on "python@3.12"

  def install
    venv = virtualenv_create(libexec, "python3.12")
    venv.pip_install buildpath
  end

  test do
    system "#{bin}/esa-tui", "--help"
  end
end


