package com.junshi.assistant;
import org.json.*;
import javax.net.ssl.HttpsURLConnection;
import java.io.*;
import java.net.URL;
import java.nio.charset.StandardCharsets;
import java.util.UUID;

public class Api {
    public final String base, token;
    public Api(String base,String token){this.base=UrlPolicy.base(base);this.token=token;}
    public Object call(String method,String path,JSONObject body) throws Exception {return send(method,path,body,null);}
    public JSONObject object(String method,String path,JSONObject body)throws Exception{return (JSONObject)call(method,path,body);}
    public JSONArray array(String path)throws Exception{return (JSONArray)call("GET",path,null);}
    public Object send(String method,String path,JSONObject body,Media item)throws Exception {
        if(!path.startsWith("/") || path.contains(".."))throw new IOException("无效接口路径");
        HttpsURLConnection c=(HttpsURLConnection)new URL(base+"/api/v1"+path).openConnection();
        c.setInstanceFollowRedirects(false);c.setConnectTimeout(15000);c.setReadTimeout(300000);c.setRequestMethod(method);
        if(token!=null)c.setRequestProperty("Authorization","Bearer "+token);
        try{
            if(item!=null){
                String boundary="junshi"+UUID.randomUUID();c.setDoOutput(true);c.setChunkedStreamingMode(65536);
                c.setRequestProperty("Content-Type","multipart/form-data; boundary="+boundary);
                try(OutputStream out=c.getOutputStream()){
                    for(String key:new String[]{"operation_id","sent_at"})write(out,"--"+boundary+"\r\nContent-Disposition: form-data; name=\""+key+"\"\r\n\r\n"+body.getString(key)+"\r\n");
                    write(out,"--"+boundary+"\r\nContent-Disposition: form-data; name=\"file\"; filename=\"attachment."+item.extension()+"\"\r\nContent-Type: "+item.mime+"\r\n\r\n");
                    try(InputStream in=new FileInputStream(item.file)){byte[] b=new byte[65536];int n;while((n=in.read(b))!=-1)out.write(b,0,n);}
                    write(out,"\r\n--"+boundary+"--\r\n");
                }
            }else if(body!=null){c.setDoOutput(true);c.setRequestProperty("Content-Type","application/json; charset=utf-8");try(OutputStream out=c.getOutputStream()){write(out,body.toString());}}
            int status=c.getResponseCode();
            if(status>=300 && status<400)throw new IOException("服务器发生重定向，请使用正确的 HTTPS 地址重新登录。");
            InputStream stream=status>=400?c.getErrorStream():c.getInputStream();
            String result=read(stream);
            if(status>=400){
                if(status==401)throw new IOException("登录已失效，请回到 App 重新登录。");
                String detail="服务器返回 HTTP "+status;
                try{Object d=new JSONObject(result).opt("detail");if(d instanceof String)detail=(String)d;}catch(JSONException ignored){}
                throw new IOException(detail);
            }
            return result.isEmpty()?null:new JSONTokener(result).nextValue();
        }catch(java.net.SocketTimeoutException e){throw new IOException("请求超时，已保存的记录会保留；保持本次输入重试，避免重复导入。");}
        finally{c.disconnect();}
    }
    private static void write(OutputStream out,String text)throws IOException{out.write(text.getBytes(StandardCharsets.UTF_8));}
    private static String read(InputStream stream)throws IOException{
        if(stream==null)return "";try(InputStream in=stream;ByteArrayOutputStream out=new ByteArrayOutputStream()){
            byte[] b=new byte[8192];int n,total=0;while((n=in.read(b))!=-1){total+=n;if(total>4*1024*1024)throw new IOException("服务器响应过大");out.write(b,0,n);}return out.toString("UTF-8");}
    }
    public static JSONObject json(Object... pairs)throws JSONException{JSONObject o=new JSONObject();for(int i=0;i<pairs.length;i+=2)o.put((String)pairs[i],pairs[i+1]);return o;}
}
