Output clawscript-demo.gif

Set FontSize 15
Set Width 1280
Set Height 820
Set Padding 18
Set TypingSpeed 35ms
Set Theme "Catppuccin Mocha"

Type "# 1. Validator rejects rule-breaking programs BEFORE execution"
Sleep 400ms
Enter
Sleep 900ms

Type "cat demo/bad.clw"
Enter
Sleep 1500ms

Type "python3 clw.py demo/bad.clw"
Enter
Sleep 2800ms

Type "clear"
Enter
Sleep 400ms

Type "# 2. Bounded retry + terminal invariant = clean audit trail"
Sleep 400ms
Enter
Sleep 900ms

Type "python3 clw.py examples/extract_json.clw 2>&1 | tail -22"
Enter
Sleep 4500ms

Sleep 1500ms
