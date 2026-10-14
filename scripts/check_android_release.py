"""Verify public APK metadata against the configured signing certificate."""
import hashlib,json,re,sys
from pathlib import Path
out=Path(sys.argv[1])
signature=(out/'signature.txt').read_text()
package=(out/'package.txt').read_text()
digest=hashlib.sha256(Path(sys.argv[2]).read_bytes()).hexdigest()
match=re.search(r'Signer #1 certificate SHA-256 digest: ([0-9a-fA-F]+)',signature)
assert match and match.group(1).lower()==digest, 'APK signing certificate differs from configured keystore'
assert 'CN=Android Debug' not in signature, 'Debug signing certificate is not a production release'
assert re.search(r'Verified using v2 scheme .*: true',signature), 'APK v2 signature missing'
assert "name='com.junshi.assistant'" in package
assert "versionCode='23100'" in package and "versionName='1.0.0'" in package
assert "sdkVersion:'26'" in package
assert 'application-debuggable' not in package
report={'version':'1.0.0','version_code':23100,'application_id':'com.junshi.assistant','debuggable':False,'signature_verified':True,'configured_certificate_matches':True,'certificate_sha256':digest}
(out/'release-verification.json').write_text(json.dumps(report,indent=2)+'\n')
print('Fixed certificate, production signature, version and non-debuggable APK: PASS')
