class EsaTui < Formula
  include Language::Python::Virtualenv

  desc "TUI for Alibaba Cloud ESA management"
  homepage "https://github.com/delvinwang-inno/homebrew-esa-tui"
  url "https://github.com/delvinwang-inno/homebrew-esa-tui/archive/refs/tags/v0.1.0.tar.gz"
  sha256 "7af2b51a3f71fa23bccf08cd22f83bb8de436b11692c95655b08ed791f67b9c9"
  license "MIT"
  head "https://github.com/delvinwang-inno/homebrew-esa-tui.git", branch: "main"

  depends_on "python@3.12"

  def install
    venv = virtualenv_create(libexec, "python3.12")
    venv.pip_install_and_link buildpath
  end

  test do
    system "#{bin}/esa-tui", "--help"
  end
end


