package com.junshi.assistant;
import android.content.Context;
import android.net.Uri;
import java.io.*;
import java.util.*;

public final class Media {
    public final File file;
    public final String mime;
    public Media(File file,String mime){this.file=file;this.mime=mime;}
    public String extension(){return switch(mime){case "image/png"->"png";case "image/jpeg"->"jpg";case "image/gif"->"gif";case "image/webp"->"webp";case "video/mp4"->"mp4";case "video/webm"->"webm";case "video/quicktime"->"mov";default->throw new IllegalArgumentException("暂不支持此附件格式");};}
    public static Media copy(Context context,Uri uri)throws Exception{
        if(uri==null || !"content".equals(uri.getScheme()))throw new IOException("只能导入系统分享或文件选择器提供的附件。");
        String type=context.getContentResolver().getType(uri);
        File dir=new File(context.getCacheDir(),"imports");if(!dir.exists()&&!dir.mkdirs())throw new IOException("无法准备附件缓存");
        Media item=new Media(new File(dir,UUID.randomUUID().toString()),type==null?"":type);item.extension();
        try(InputStream in=context.getContentResolver().openInputStream(uri);OutputStream out=new FileOutputStream(item.file)){
            if(in==null)throw new IOException("无法读取附件");byte[] b=new byte[65536];int n;long total=0;
            while((n=in.read(b))!=-1){total+=n;if(total>50L*1024*1024)throw new IOException("每个附件最多 50 MB");out.write(b,0,n);}if(total==0)throw new IOException("附件为空");
        }catch(Exception e){item.file.delete();throw e;}return item;
    }
    public static void cleanup(Context c){File[] files=new File(c.getCacheDir(),"imports").listFiles();if(files!=null)for(File f:files)if(f.isFile())f.delete();}
}
