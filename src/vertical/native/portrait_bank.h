/* Included only by the generated portrait resource worker. */
#include PATCH_MANIFEST
static u8 portrait_expected[4096],portrait_actual[4096];
static const char *portrait_tmp[3]={"/usr/share/app/.a7c2-portrait-00.tmp","/usr/share/app/.a7c2-portrait-01.tmp","/usr/share/app/.a7c2-portrait-02.tmp"};
static i64 portrait_guard(u32 i,i64 fd) {
 if(original[i].size!=(i64)portrait_source_sizes[i])return -116;
 for(u32 n=0;n<portrait_edit_counts[i];n++) {
  const struct PortraitEdit *e=portrait_edits[i]+n;u8 old[12];
  if(sc(67,fd,(i64)old,12,e->at,0,0)!=12)return -5;
  if(!rs_same(old,e->old,12))return -116;
 }
 return 0;
}
static i64 portrait_chunk(u32 i,i64 source,u64 at,u32 n) {
 u64 size=portrait_source_sizes[i];u32 from=at<size?(size-at<n?size-at:n):0;
 if(from&&sc(67,source,(i64)portrait_expected,from,at,0,0)!=(i64)from)return -5;
 for(u32 k=0;k<portrait_edit_counts[i];k++) {
  const struct PortraitEdit *e=portrait_edits[i]+k;
  for(u32 b=0;b<12;b++)if(e->at+b>=at&&e->at+b<at+from)portrait_expected[e->at+b-at]=e->value[b];
 }
 for(u32 b=from;b<n;b++)portrait_expected[b]=portrait_tails[i][at+b-size];
 return 0;
}
static i64 portrait_compare_part(u32 i,const char *path,int partial) {
 i64 a=op(src[i],0x20000),b=-1,err=0;if(a<0)return a;
 b=op(path,0x20000);if(b<0){cl(a);return b;}
 struct RsStat st;err=sc(80,b,(i64)&st,0,0,0,0);
 u64 total=portrait_source_sizes[i]+portrait_tail_sizes[i];
 if(!err&&((st.mode&0170000)!=0100000||st.size<0||st.size>(i64)total||(!partial&&st.size!=(i64)total)))err=-17;
 if(!err&&partial)total=st.size;
 if(!err)err=portrait_guard(i,a);
 for(u64 at=0;at<total&&!err;at+=4096) {
  u32 n=total-at<4096?total-at:4096;err=portrait_chunk(i,a,at,n);
  if(!err&&sc(67,b,(i64)portrait_actual,n,at,0,0)!=(i64)n)err=-5;
  if(!err&&!rs_same(portrait_expected,portrait_actual,n))err=-17;
 }
 cl(a);cl(b);return err;
}
static i64 portrait_compare(u32 i,const char *path){return portrait_compare_part(i,path,0);}
static i64 portrait_create(u32 i) {
 if(!portrait_tail_sizes[i])return sc(36,(i64)target[i],-100,(i64)dst[i],0,0,0);
 i64 a=op(src[i],0x20000);if(a<0)return a;
 /* Exclusive temporary creation, then complete verification and atomic rename.
  * An existing symlink is replaced without ever writing through it. */
 i64 b=sc(56,-100,(i64)portrait_tmp[i],0x200c1,0600,0,0);
 if(b==-17) {
  /* A power loss may leave our temporary prefix. Reuse no previous request;
   * only remove bytes which exactly match the newly derived target prefix. */
  i64 old=portrait_compare_part(i,portrait_tmp[i],1);
  if(old){cl(a);return old;}
  old=sc(35,-100,(i64)portrait_tmp[i],0,0,0,0);
  if(old){cl(a);return old;}
  b=sc(56,-100,(i64)portrait_tmp[i],0x200c1,0600,0,0);
 }
 if(b<0){cl(a);return b;}
 i64 err=portrait_guard(i,a);u64 total=portrait_source_sizes[i]+portrait_tail_sizes[i];
 for(u64 at=0;at<total&&!err;at+=4096) {
  u32 n=total-at<4096?total-at:4096;err=portrait_chunk(i,a,at,n);
  if(!err&&sc(64,b,(i64)portrait_expected,n,0,0,0)!=(i64)n)err=-5;
 }
 if(!err)err=sc(55,b,original[i].uid,original[i].gid,0,0,0);
 if(!err)err=sc(52,b,original[i].mode&0777,0,0,0,0);
 if(!err)err=sc(82,b,0,0,0,0,0);
 cl(a);cl(b);
 if(!err)err=portrait_compare(i,portrait_tmp[i]);
 if(!err)err=sc(38,-100,(i64)portrait_tmp[i],-100,(i64)dst[i],0,0);
 if(err)sc(35,-100,(i64)portrait_tmp[i],0,0,0,0);
 return err;
}
