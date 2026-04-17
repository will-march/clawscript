Output clawscript-demo.gif

Set FontSize 22
Set Width 1400
Set Height 900
Set Padding 24
Set TypingSpeed 28ms
Set Theme "Catppuccin Mocha"

Type "# 1. The validator rejects rule-breaking programs"
Enter
Sleep 900ms

Type "cat demo/bad.clw"
Enter
Sleep 1800ms

Type "python3 clw.py demo/bad.clw"
Enter
Sleep 3000ms

Type "clear"
Enter
Sleep 500ms

Type "# 2. Micro JSON extraction with traced invariants"
Enter
Sleep 900ms

Type "cat demo/micro_extract.clw"
Enter
Sleep 3200ms

Type "python3 clw.py demo/micro_extract.clw | grep -E 'checkpoint|invariant_ok|prompt_begin|tool_begin|Ada|program_end'"
Enter
Sleep 4800ms

Sleep 1600ms
