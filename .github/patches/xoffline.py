from pathlib import Path


PATH = Path.cwd() / "flutter/lib/common/widgets/peer_card.dart"


def main() -> None:
    text = PATH.read_text(encoding="utf-8")
    if "Icons.close" in text and "online ? CircleAvatar" in text:
        print("Offline X marker is already present.")
        return
    old = """          child: CircleAvatar(
              radius: 3, backgroundColor: online ? Colors.green : kColorWarn)))"""
    new = """          child: online
              ? CircleAvatar(radius: 3, backgroundColor: Colors.green)
              : Icon(
                  Icons.close,
                  color: Colors.red,
                  size: 12.0,
                )))"""
    if old not in text:
        raise SystemExit("Could not find online status marker in peer_card.dart")
    PATH.write_text(text.replace(old, new, 1), encoding="utf-8")
    print("Changed offline status to a red X marker.")


if __name__ == "__main__":
    main()
