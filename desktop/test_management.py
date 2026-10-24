import time
import tkinter as tk
import unittest
from unittest.mock import Mock
from assistant import Assistant
from management import PersonDialog, AccountDialog, ModelDialog, create_person_with_conversation, model_payload, scrollable


class WorkflowTests(unittest.TestCase):
    def test_person_kept_when_conversation_retry_is_needed(self):
        client=Mock();state={}
        client.request.side_effect=[{'id':'p','name':'A'},[],ValueError('timeout'),[],{'id':'c','title':'Named'}]
        with self.assertRaises(ValueError):create_person_with_conversation(client,state,'A','','Named')
        self.assertEqual(create_person_with_conversation(client,state,'A','','Named')[1]['id'],'c')
        self.assertEqual(sum(c.args[:2]==('POST','/persons') for c in client.request.call_args_list),1)

    def test_lost_conversation_response_is_reconciled(self):
        client=Mock();state={'person':{'id':'p'}}
        client.request.return_value=[{'id':'c','title':'Named'}]
        self.assertEqual(create_person_with_conversation(client,state,'A','','Named')[1]['id'],'c')
        self.assertEqual(client.request.call_count,1)

    def test_unknown_person_creation_does_not_repeat(self):
        client=Mock();client.request.side_effect=ValueError('timeout');state={}
        for _ in range(2):
            with self.assertRaises(ValueError):create_person_with_conversation(client,state,'A','','Named')
        self.assertEqual(client.request.call_count,1)

    def test_empty_names_do_not_write(self):
        client=Mock()
        with self.assertRaises(ValueError):create_person_with_conversation(client,{},'A','',' ')
        client.request.assert_not_called()

    def test_existing_model_key_is_preserved(self):
        values={'name':'Qwen','provider':'qwen','base_url':'https://example.com/v1','model':'example-model','api_key':'','timeout_seconds':'60'}
        self.assertNotIn('api_key',model_payload(values,editing=True))
        with self.assertRaises(ValueError):model_payload(values)
        with self.assertRaises(ValueError):model_payload({**values,'timeout_seconds':'nan'},editing=True)


class NativeManagementTests(unittest.TestCase):
    def setUp(self):
        self.root=tk.Tk();self.app=Assistant(self.root,hotkey=False);self.client=Mock();self.app.client=self.client
        self.root.update()

    def tearDown(self):
        self.app.closed=True
        for callback in self.root.tk.call('after','info'):self.root.after_cancel(callback)
        self.root.destroy()

    def settle(self):
        until=time.monotonic()+5
        while self.app.busy and time.monotonic()<until:self.root.update();time.sleep(.02)
        self.assertFalse(self.app.busy)

    def test_person_creation_selects_named_first_conversation(self):
        self.client.request.side_effect=[{'id':'p','name':'Synthetic','nickname':None},[],{'id':'c','title':'First chat'}]
        dialog=PersonDialog(self.app);dialog.name.insert(0,'Synthetic');dialog.title.delete(0,'end');dialog.title.insert(0,'First chat')
        dialog.save();self.settle()
        self.assertEqual(self.app.selected_person(),'p');self.assertEqual(self.app.conversation.get(),'First chat')
        self.assertIsNone(self.app.active_dialog)

    def test_new_platform_binds_current_conversation(self):
        self.app.people=[{'id':'p','name':'A'}];self.app.person['values']=['A'];self.app.person.current(0)
        self.app.account['values']=['Unmarked'];self.app.account.current(0)
        self.app.conversations=[{'id':'c','title':'First'}];self.app.conversation['values']=['First'];self.app.conversation.current(0)
        account={'id':'a','platform':'wechat','account_handle':'synthetic','display_name':''}
        def request(method,path,payload=None):
            if method=='GET' and path.endswith('platform-accounts'):return [account] if getattr(self,'created',False) else []
            if method=='POST':self.created=True;return account
            if method=='PUT':return account
            if path.startswith('/conversations?'):return [{'id':'c','title':'First'}]
            if path.endswith('platform-source'):return account
            raise AssertionError(path)
        self.client.request.side_effect=request
        dialog=AccountDialog(self.app);dialog.handle.insert(0,'synthetic');dialog.save();self.settle()
        self.assertEqual(self.app.selected_account(),'a');self.assertEqual(self.app.conversation.get(),'First')
        self.client.request.assert_any_call('PUT','/conversations/c/platform-source',{'account_id':'a'})

    def test_model_edit_preserves_key_and_activation_is_explicit(self):
        profile={'id':'m','name':'Model','provider':'qwen','base_url':'https://example.com/v1','model':'sample','timeout_seconds':60,'is_active':False}
        def request(method,path,payload=None):
            if path=='/settings/llm/profiles':return [profile]
            if path=='/settings/llm/vision':return None
            if method=='PUT':return profile
            if path.endswith('/activate'):return {**profile,'is_active':True}
            raise AssertionError(path)
        self.client.request.side_effect=request
        dialog=ModelDialog(self.app);self.settle();dialog.selector.current(1);dialog.select();dialog.save();self.settle()
        puts=[c for c in self.client.request.call_args_list if c.args[0]=='PUT']
        self.assertNotIn('api_key',puts[0].args[2])
        self.assertFalse(any(c.args[0]=='POST' for c in self.client.request.call_args_list))
        dialog.action('activate');self.settle()
        self.client.request.assert_any_call('POST','/settings/llm/profiles/m/activate')
        dialog.close()


if __name__=='__main__':unittest.main()


class SectionTests(unittest.TestCase):
    def test_toggle_flips_the_caption_and_the_body(self):
        import tkinter as tk
        from management import Section
        root = tk.Tk(); root.withdraw()
        try:
            section = Section(root, '分组', open=True)
            self.assertEqual(section.body.winfo_manager(), 'pack')
            self.assertTrue(section.caption.cget('text').startswith('\u25be'))
            section.toggle()
            self.assertEqual(section.body.winfo_manager(), '')
            self.assertTrue(section.caption.cget('text').startswith('\u25b8'))
            section.toggle()
            self.assertEqual(section.body.winfo_manager(), 'pack')
            self.assertTrue(section.caption.cget('text').startswith('\u25be'))
        finally:
            root.destroy()


class EventPumpTests(unittest.TestCase):
    def test_a_raising_callback_does_not_stop_the_pump(self):
        import queue
        from assistant import drain_events
        events, seen = queue.Queue(), []
        events.put(lambda: (_ for _ in ()).throw(RuntimeError('boom')))
        events.put(lambda: seen.append('next'))
        drain_events(events, lambda: seen.append('reported'))
        self.assertEqual(seen, ['reported', 'next'])
        self.assertTrue(events.empty())

    def test_a_failing_result_callback_leaves_the_dialog_usable(self):
        root = tk.Tk()
        app = Assistant(root, hotkey=False)
        try:
            dialog = PersonDialog(app)

            def boom(_result):
                raise RuntimeError('界面更新炸了')

            dialog.perform(lambda: {'ok': True}, boom)
            until = time.monotonic() + 5
            while dialog.busy and time.monotonic() < until:
                app.poll(); root.update(); time.sleep(.02)
            self.assertFalse(dialog.busy)
            for widget, state in dialog.widgets:
                self.assertEqual(str(widget.cget('state')), state)
            dialog.close()
        finally:
            app.closed = True
            root.destroy()


class ScrollTests(unittest.TestCase):
    def test_wheel_scrolls_the_panel_and_teardown_is_quiet(self):
        from tkinter import ttk
        root = tk.Tk(); root.withdraw()
        holder = ttk.Frame(root); holder.pack(fill='both', expand=True)
        inner = scrollable(holder)
        for _ in range(40):
            ttk.Label(inner, text='一行内容').pack()
        root.update()
        inner.event_generate('<MouseWheel>', delta=-120)
        root.update()
        root.destroy()

    def test_wheel_after_teardown_does_not_raise(self):
        import management
        from tkinter import ttk
        root = tk.Tk(); root.withdraw()
        holder = ttk.Frame(root); holder.pack()
        inner = scrollable(holder)
        key = str(inner)
        root.destroy()
        self.assertNotIn(key, management._SCROLL_TARGETS)
