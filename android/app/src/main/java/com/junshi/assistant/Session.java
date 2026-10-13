package com.junshi.assistant;
import android.app.Application;
import android.os.Handler;
import android.os.Looper;
import org.json.*;
import java.util.*;
import java.util.concurrent.*;
import java.time.*;
import java.util.function.Consumer;

public class Session extends Application {
    public Api api;
    public boolean busy;
    public String input="",draft="",status="登录后选择人物，再导入聊天内容。",person="",conversation="",account="";
    public JSONArray people=new JSONArray(),conversations=new JSONArray(),accounts=new JSONArray();
    public final List<Media> media=new ArrayList<>();
    public Job job;
    public long epoch=0;
    private final List<Runnable> listeners=new ArrayList<>();
    public final ExecutorService executor=Executors.newSingleThreadExecutor();
    private final Handler main=new Handler(Looper.getMainLooper());
    public interface Work<T>{T run()throws Exception;}
    @Override public void onCreate(){super.onCreate();Media.cleanup(this);}
    public void listen(Runnable r){listeners.add(r);}
    public void unlisten(Runnable r){listeners.remove(r);}
    public void changed(){for(Runnable r:new ArrayList<>(listeners))r.run();}
    public void message(String s){status=s;changed();}
    public <T> void run(String message,Work<T> action,Consumer<T> done){
        if(busy)return;busy=true;status=message;long version=epoch;changed();
        executor.execute(()->{try{T value=action.run();main.post(()->{if(version!=epoch)return;busy=false;try{done.accept(value);}catch(Exception e){status="操作结果处理失败，请刷新核对。";}changed();});}
        catch(Exception e){main.post(()->{if(version!=epoch)return;busy=false;status=e instanceof java.io.IOException || e instanceof IllegalArgumentException?e.getMessage():"操作未完成，请检查服务器配置后重试。";changed();});}});
    }
    public void logout(){epoch++;api=null;busy=false;person=conversation=account=input=draft="";people=accounts=conversations=new JSONArray();job=null;media.clear();Media.cleanup(this);status="已退出登录。";changed();}
    public void editInput(String s){if(!input.equals(s)){input=s;job=null;}}
    public void clearDraft(){if(busy)return;input=draft="";job=null;for(Media m:media)m.file.delete();media.clear();changed();}
    public void loadPeople(){if(api==null)return;Api client=api;run("正在加载人物…",()->client.array("/persons"),result->{people=result;person=account=conversation="";accounts=conversations=new JSONArray();job=null;status="请选择人物。";});}
    public void selectPerson(String id){
        if(busy||api==null||id.equals(person))return;person=id;account=conversation="";accounts=conversations=new JSONArray();job=null;
        Api client=api;run("正在加载会话与平台…",()->new JSONArray[]{client.array("/persons/"+id+"/platform-accounts"),client.array("/conversations?person_id="+id)},r->{accounts=r[0];conversations=r[1];status="请选择会话；平台信息随会话显示。";});
    }
    public void selectConversation(String id){if(busy||api==null||id.equals(conversation))return;conversation=id;job=null;Api client=api;run("正在核对会话来源…",()->client.call("GET","/conversations/"+id+"/platform-source",null),o->{account=o instanceof JSONObject?((JSONObject)o).optString("id"):"";status="已选择会话，可以导入内容。";});}
    public String platformText(){for(int i=0;i<accounts.length();i++){JSONObject a=accounts.optJSONObject(i);if(a!=null&&account.equals(a.optString("id")))return a.optString("platform")+" · "+a.optString("display_name",a.optString("account_handle"));}return "平台：未标注（可在人物管理中添加）";}
    public void generate(){
        if(api==null||conversation.isEmpty()){message("请先登录并选择人物、会话。");return;}
        if(input.trim().isEmpty()&&media.isEmpty()){message("请先粘贴文字或选择附件。");return;}
        if(job==null)job=new Job(person,conversation,input,new ArrayList<>(media));
        Job current=job;Api client=api;
        run("正在保存内容并生成回复，请稍候…",()->current.generate(client),text->{draft=text;status="建议已生成。实际发送后再点“确认已发送”。";
            executor.execute(()->{try{client.call("POST","/persons/"+current.person+"/memory/refresh",null);}catch(Exception e){main.post(()->{if(job==current&&api==client)message("建议已保留；长期档案更新未完成，可在主页面重试。");});}});
        });
    }
    public void confirm(){
        if(job==null||draft.trim().isEmpty()){message("请先生成回复。");return;}Job current=job;Api client=api;String text=draft;
        run("正在登记已发送内容…",()->current.confirm(client,text),v->{status=v?"已登记为我发送的消息。":"这条回复已登记，无需重复确认。";});
    }
    public static class Job {
        final String person,conversation,text,time=OffsetDateTime.now(ZoneOffset.ofHours(8)).toString(),messageId=UUID.randomUUID().toString(),confirmId=UUID.randomUUID().toString();
        final List<Media> media;final List<String> operations=new ArrayList<>();final Map<Integer,String> uploads=new HashMap<>();final Set<Integer> analyzed=new HashSet<>();
        boolean saved,confirmed;String confirmedText,confirmedTime;
        Job(String person,String conversation,String text,List<Media> media){this.person=person;this.conversation=conversation;this.text=text;this.media=media;for(Media ignored:media)operations.add(UUID.randomUUID().toString());}
        String generate(Api api)throws Exception{
            if(!text.trim().isEmpty()&&!saved){api.call("POST","/pc/messages",Api.json("operation_id",messageId,"conversation_id",conversation,"sender_type","person","content",text,"sent_at",time));saved=true;}
            for(int i=0;i<media.size();i++){
                if(!uploads.containsKey(i)){JSONObject r=(JSONObject)api.send("POST","/pc/conversations/"+conversation+"/media",Api.json("operation_id",operations.get(i),"sent_at",time),media.get(i));uploads.put(i,r.getString("id"));}
                if(!analyzed.contains(i)){api.call("POST","/media/"+uploads.get(i)+"/analyze",null);analyzed.add(i);}
            }
            String value=api.object("GET","/conversations/"+conversation+"/strategic-reply/context",null).optString("draft");
            if(value.trim().isEmpty())throw new java.io.IOException("没有返回有效回复，记录已保存，可保持输入重试。");return value;
        }
        boolean confirm(Api api,String text)throws Exception{
            if(confirmed)return false;if(confirmedText!=null&&!confirmedText.equals(text))throw new java.io.IOException("上次确认结果不确定，请保留相同回复重试或先核对主页面。");
            if(confirmedText==null){confirmedText=text;confirmedTime=OffsetDateTime.now(ZoneOffset.ofHours(8)).toString();}
            api.call("POST","/pc/messages",Api.json("operation_id",confirmId,"conversation_id",conversation,"sender_type","user","content",text,"sent_at",confirmedTime));confirmed=true;return true;
        }
    }
}
