class EsaTui < Formula
  include Language::Python::Virtualenv

  desc "TUI for Alibaba Cloud ESA management"
  homepage "https://github.com/delvinwang-inno/homebrew-esa-tui"
  url "https://github.com/delvinwang-inno/homebrew-esa-tui/archive/refs/tags/v0.1.0.tar.gz"
  sha256 "c1841b2fc8399b5761c243d7ccaa9c4caf671f6ecb6b96712ff0d285ffeea8a2"
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


