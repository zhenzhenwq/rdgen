from pathlib import Path


PATH = Path.cwd() / "flutter/lib/desktop/widgets/remote_toolbar.dart"


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if old not in text:
        raise SystemExit(f"Could not find {label}")
    return text.replace(old, new, 1)


def main() -> None:
    text = PATH.read_text(encoding="utf-8")
    if "_CycleMonitorMenu" in text:
        print("Cycle monitor button is already present.")
        return

    text = replace_once(
        text,
        """          child: _DraggableShowHide(
            id: widget.id,
""",
        """          child: _DraggableShowHide(
            id: widget.id,
            ffi: widget.ffi,
""",
        "_DraggableShowHide construction",
    )
    text = replace_once(
        text,
        """class _DraggableShowHide extends StatefulWidget {
  final String id;
""",
        """class _DraggableShowHide extends StatefulWidget {
  final String id;
  final FFI ffi;
""",
        "_DraggableShowHide ffi field",
    )
    text = replace_once(
        text,
        """  const _DraggableShowHide({
    Key? key,
    required this.id,
""",
        """  const _DraggableShowHide({
    Key? key,
    required this.id,
    required this.ffi,
""",
        "_DraggableShowHide ffi constructor parameter",
    )
    text = replace_once(
        text,
        """      children: [
        _buildDraggable(context),
""",
        """      children: [
        _buildDraggable(context),
        _CycleMonitorMenu(id: widget.id, ffi: widget.ffi),
""",
        "collapsed toolbar children",
    )
    text += """

class _CycleMonitorMenu extends StatelessWidget {
  final String id;
  final FFI ffi;

  const _CycleMonitorMenu({
    Key? key,
    required this.id,
    required this.ffi,
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
    final pi = ffi.ffiModel.pi;
    if (pi.displays.length <= 1) {
      return const Offstage();
    }
    return TextButton(
      onPressed: () {
        final display = CurrentDisplayState.find(id);
        display.value = display.value + 1;
        if (display.value >= pi.displays.length) {
          display.value = 0;
        }
        openMonitorInTheSameTab(display.value, ffi, pi);
      },
      child: Stack(children: [
        Container(
            child: Align(
                alignment: Alignment.center,
                child: const Icon(
                  Icons.personal_video,
                  color: _ToolbarTheme.blueColor,
                  size: 20.0,
                ))),
        Container(
            child: Align(
                alignment: Alignment(0.0, -0.4),
                child: Obx(() => Text(
                      '  ${CurrentDisplayState.find(id).value + 1}/${pi.displays.length}',
                      style: const TextStyle(
                          color: _ToolbarTheme.blueColor, fontSize: 8),
                    )))),
      ]),
    );
  }
}
"""
    PATH.write_text(text, encoding="utf-8")
    print("Added the cycle monitor button.")


if __name__ == "__main__":
    main()
