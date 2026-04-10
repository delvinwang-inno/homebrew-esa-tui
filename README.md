# esa-tui
ESA-TUI for quick access to Alibaba Cloud ESA.

## Installation via Homebrew

To install `esa-tui` using Homebrew, you can tap this repository:

```bash
brew tap delvinwang/esa-tui
brew install esa-tui
```

### For Developers (Homebrew Tap Setup)

If you are the maintainer and want to update the tap:

1.  **Tag a release:**
    ```bash
    git tag v0.1.0
    git push origin v0.1.0
    ```

2.  **Get the SHA256:**
    ```bash
    curl -L https://github.com/delvinwang/homebrew-esa-tui/archive/refs/tags/v0.1.0.tar.gz | shasum -a 256
    ```

3.  **Update `Formula/esa-tui.rb`:**
    Update the `url` and `sha256` in the formula.

4.  **Test the formula:**
    ```bash
    brew test Formula/esa-tui.rb
    ```

