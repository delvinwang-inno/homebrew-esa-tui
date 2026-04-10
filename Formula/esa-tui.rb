class EsaTui < Formula
  include Language::Python::Virtualenv

  desc "TUI for Alibaba Cloud ESA management"
  homepage "https://github.com/delvinwang-inno/homebrew-esa-tui"
  url "https://github.com/delvinwang-inno/homebrew-esa-tui/archive/refs/tags/v0.1.0.tar.gz"
  sha256 "0019dfc4b32d63c1392aa264aed2253c1e0c2fb09216f8e2cc269bbfb8bb49b5"
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


