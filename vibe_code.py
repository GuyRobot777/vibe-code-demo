"""
vibe_code.py - Vibe coding engine.
Describe what you want. The agent writes it. You review it. It runs.
Demonstrates the vibe coding methodology in Ford's Studio Engineer role.
"""

import ast, json, os, subprocess, sys, tempfile, urllib.request

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")

SYSTEM = ("Expert Python developer as vibe coding agent. "
          "User describes a tool in plain English. Write clean Python 3.11+. "
          "Standard library only unless user asks for third-party packages. "
          "Include docstring and main block. Respond with ONLY Python code, no markdown.")

DANGEROUS = ["os.system(","eval(","exec(","shutil.rmtree","__import__("]

def call_claude(prompt: str) -> str:
    payload = json.dumps({"model":"claude-3-5-sonnet-20241022","max_tokens":2048,
        "system":SYSTEM,"messages":[{"role":"user","content":prompt}]}).encode()
    req = urllib.request.Request("https://api.anthropic.com/v1/messages", data=payload,
        headers={"x-api-key":ANTHROPIC_API_KEY,"anthropic-version":"2023-06-01","content-type":"application/json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read())["content"][0]["text"].strip()

def check_syntax(code):
    try: ast.parse(code); return True, "PASS"
    except SyntaxError as e: return False, f"Line {e.lineno}: {e.msg}"

def safety_scan(code):
    found = [p for p in DANGEROUS if p in code]
    return not found, found

def preview(code, n=15):
    lines = code.split("\n")
    print(f"\n--- Preview ({min(n,len(lines))} of {len(lines)} lines) ---")
    for l in lines[:n]: print(f"  {l}")
    if len(lines)>n: print(f"  ...({len(lines)-n} more lines)")
    print("---\n")

def run_code(code, name):
    with tempfile.NamedTemporaryFile(mode="w",suffix=".py",delete=False,prefix=name+"_") as f:
        f.write(code); tmp=f.name
    print(f"\n[RUNNING] {tmp}\n"+"-"*40)
    try: subprocess.run([sys.executable,tmp],check=False)
    except KeyboardInterrupt: print("\n[STOPPED]")
    finally: os.unlink(tmp)

def save_code(code, name):
    fn = name.lower().replace(" ","_")[:40]+".py"
    with open(fn,"w") as f: f.write(code)
    return fn

def main():
    print("="*50+"\n  VIBE CODE ENGINE\n  Describe it. Review it. Run it.\n"+"="*50)
    while True:
        print()
        desc = input("What do you want to build? (quit to exit) > ").strip()
        if desc.lower() in ("quit","exit","q",""): break
        print("\n[AGENT] Generating code...")
        try: code = call_claude(desc)
        except Exception as e: print(f"[ERROR] {e}"); continue
        ok, smsg = check_syntax(code)
        safe, flagged = safety_scan(code)
        print(f"[AGENT] Syntax: {smsg} | Safety: {'PASS' if safe else 'FLAGGED: '+str(flagged)}")
        if not ok:
            print("[AGENT] Auto-fixing...")
            code = call_claude(f"Fix this Python, return ONLY corrected code:\n{code}\nError: {smsg}")
            ok, smsg = check_syntax(code); print(f"[AGENT] Re-check: {smsg}")
        if not safe:
            if input("Unsafe patterns. Proceed? [y/N] ").strip().lower()!="y": continue
        name = desc[:30].replace(" ","_")
        print(f"[AGENT] Generated: {name}.py ({len(code.splitlines())} lines)")
        if input("Preview? [Y/n] ").strip().lower()!="n": preview(code)
        if input("Save? [Y/n] ").strip().lower()!="n": print(f"[SAVED] {save_code(code,name)}")
        if input("Run? [y/N] ").strip().lower()=="y": run_code(code,name)
        print("\n[DONE]")

if __name__ == "__main__":
    main()
