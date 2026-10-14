"""Server-only administrator setup and cleanup recovery; never creates accounts."""
import argparse
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'backend'))
from app.core.database import get_connection
from app.services.account_deletion import finish_cleanup

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--grant-admin',metavar='EXISTING_USERNAME')
    parser.add_argument('--retry-cleanup',metavar='JOB_ID')
    args=parser.parse_args()
    if bool(args.grant_admin)==bool(args.retry_cleanup): parser.error('Select exactly one action')
    if args.retry_cleanup:
        finish_cleanup(args.retry_cleanup);print('附件清理完成');return
    with get_connection() as conn:
        conn.execute('BEGIN IMMEDIATE')
        row=conn.execute('SELECT user_id FROM user_credentials WHERE username=?',(args.grant_admin.strip().lower(),)).fetchone()
        if row is None: raise SystemExit('账号不存在，请先正常注册')
        conn.execute('INSERT INTO account_identities(user_id,administrator,disabled) VALUES(?,1,0) ON CONFLICT(user_id) DO UPDATE SET administrator=1,disabled=0',(row[0],))
        from app.services.account_identity import AccountIdentityService
        AccountIdentityService().audit(conn,'server-console',row[0],'grant:admin','服务器管理员初始化')
    print('管理员权限已授予现有账号')

if __name__=='__main__': main()
