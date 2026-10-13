package com.junshi.assistant;
import android.content.*;
import android.view.*;
import android.widget.*;
import android.text.*;
import org.json.*;

/** One workspace shared by the activity and the explicitly enabled overlay. */
public class Workspace extends LinearLayout {
    final Session session; final EditText input,reply; final Spinner people,conversations;
    final TextView status,attachments; boolean rendering;
    final Runnable listener=this::refresh;
    public Workspace(Context context){super(context);session=(Session)context.getApplicationContext();setOrientation(VERTICAL);setPadding(16,12,16,12);setBackgroundColor(0xfff1f8ff);
        people=new Spinner(context);conversations=new Spinner(context);addView(people);addView(conversations);
        people.setOnItemSelectedListener(selection(()->choose(people,session.people,true)));
        conversations.setOnItemSelectedListener(selection(()->choose(conversations,session.conversations,false)));
        input=new EditText(context);input.setHint("粘贴对方内容，或从其他应用分享图片、视频");input.setMinLines(2);input.setMaxLines(4);addView(input);
        input.addTextChangedListener(watch(()->{if(!rendering)session.editInput(input.getText().toString());}));
        attachments=new TextView(context);addView(attachments);
        LinearLayout actions=new LinearLayout(context);addView(actions);
        button(actions,"粘贴",()->{ClipboardManager cm=(ClipboardManager)context.getSystemService(Context.CLIPBOARD_SERVICE);if(cm.hasPrimaryClip()){ClipData clip=cm.getPrimaryClip();if(clip!=null&&clip.getItemCount()>0){CharSequence text=clip.getItemAt(0).getText();if(text!=null)input.setText(text);else session.message("图片或视频请使用分享入口或附件按钮。");}}});
        button(actions,"生成",session::generate);button(actions,"清空",session::clearDraft);
        reply=new EditText(context);reply.setHint("回复建议会显示在这里");reply.setMinLines(2);reply.setMaxLines(5);addView(reply);
        reply.addTextChangedListener(watch(()->{if(!rendering)session.draft=reply.getText().toString();}));
        LinearLayout footer=new LinearLayout(context);addView(footer);
        button(footer,"一键复制",()->{((ClipboardManager)context.getSystemService(Context.CLIPBOARD_SERVICE)).setPrimaryClip(ClipData.newPlainText("回复建议",session.draft));session.message("已复制；实际发送后再确认。");});
        button(footer,"确认已发送",session::confirm);
        status=new TextView(context);status.setTextColor(0xff31516e);addView(status);refresh();
    }
    static TextWatcher watch(Runnable r){return new TextWatcher(){public void beforeTextChanged(CharSequence s,int a,int c,int f){}public void onTextChanged(CharSequence s,int a,int b,int c){r.run();}public void afterTextChanged(Editable e){}};}
    static AdapterView.OnItemSelectedListener selection(Runnable r){return new AdapterView.OnItemSelectedListener(){public void onItemSelected(AdapterView<?> p,View v,int pos,long id){r.run();}public void onNothingSelected(AdapterView<?> p){}};}
    void choose(Spinner spinner,JSONArray data,boolean person){if(rendering||session.busy)return;int i=spinner.getSelectedItemPosition()-1;if(i>=0){JSONObject o=data.optJSONObject(i);if(o!=null){if(person)session.selectPerson(o.optString("id"));else session.selectConversation(o.optString("id"));}}}
    void populate(Spinner spinner,JSONArray data,String selected,String field,String hint){java.util.List<String> labels=new java.util.ArrayList<>();labels.add(hint);int pos=0;for(int i=0;i<data.length();i++){JSONObject o=data.optJSONObject(i);labels.add(o.optString(field));if(selected.equals(o.optString("id")))pos=i+1;}spinner.setAdapter(new ArrayAdapter<>(getContext(),android.R.layout.simple_spinner_dropdown_item,labels));spinner.setSelection(pos,false);}
    void refresh(){rendering=true;populate(people,session.people,session.person,"name","选择人物");populate(conversations,session.conversations,session.conversation,"title","选择会话");if(!input.getText().toString().equals(session.input))input.setText(session.input);if(!reply.getText().toString().equals(session.draft))reply.setText(session.draft);attachments.setText(session.platformText()+" · 附件 "+session.media.size()+" 个");status.setText(session.status);enable(this,!session.busy&&session.api!=null);rendering=false;}
    static void enable(View v,boolean enabled){v.setEnabled(enabled);if(v instanceof ViewGroup){ViewGroup g=(ViewGroup)v;for(int i=0;i<g.getChildCount();i++)enable(g.getChildAt(i),enabled);}}
    public static Button button(LinearLayout row,String text,Runnable action){Button b=new Button(row.getContext());b.setText(text);b.setAllCaps(false);row.addView(b,new LinearLayout.LayoutParams(0,LayoutParams.WRAP_CONTENT,1));b.setOnClickListener(v->action.run());return b;}
    @Override protected void onAttachedToWindow(){super.onAttachedToWindow();session.listen(listener);refresh();}
    @Override protected void onDetachedFromWindow(){session.unlisten(listener);super.onDetachedFromWindow();}
}
