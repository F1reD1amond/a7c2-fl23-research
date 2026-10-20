/* First-install/remove of two fixed private sound files. No AP/CP program or
 * setting writes. The host must install files before the boot hook, and remove
 * the boot hook before removing files. Mode0 checks, mode1 creates, mode2 removes.
 */
#define _init files_base_init
#include "probe.c"
#undef _init
#include PATCH_MANIFEST

static const char *paths[]={"/usr/share/avsystemsound/custom-shutter.bin",
                           "/usr/share/avsystemsound/custom.txt"};
static u8 scratch[65536];
struct FilesReport {
    u8 magic[8];u32 version,mode,phase,created;
    i64 status,rollback,remount,readonly,cleanup,euid,pid,model_status;
};
static struct FilesReport out;
static u64 owned_dev[2],owned_ino[2];
_Static_assert(sizeof(struct FilesReport)==88,"Sound files report ABI");
static int equal(const u8*a,const u8*b,u32 n) {
    for(u32 i=0;i<n;i++)if(a[i]!=b[i])return 0;return 1;
}
static i64 close_file(i64 *fd) {
    if(*fd<0)return 0;i64 v=sc(57,*fd,0,0,0,0,0);*fd=-1;return v;
}
static i64 stat_file(i64 fd,u64 *st) {
    i64 v=sc(80,fd,(i64)st,0,0,0,0);if(v)return v;
    return (((u32*)st)[4]&0170000)==0100000?0:-22;
}
static i64 mount_state(int ro) {
    i64 n=read_all("/proc/mounts",mounts,sizeof(mounts));if(n<0)return n;
    const u8 prefix[]="/dev/nflasha15 /usr ext2 ";u32 size=sizeof(prefix)-1,matches=0;
    for(u32 i=0;i+size+3<=(u32)n;i++)if((!i||mounts[i-1]=='\n')&&equal(mounts+i,prefix,size)) {
        if(mounts[i+size]!='r'||mounts[i+size+1]!=(ro?'o':'w')||mounts[i+size+2]!=',')return -30;
        matches++;
    }
    return matches==1?0:-22;
}
static i64 remount(int ro) {
    i64 v=sc(40,0,(i64)"/usr",0,0xc30UL+(ro?1:0),0,0);return v?v:mount_state(ro);
}
static i64 check(u32 index,int installed) {
    i64 fd=op(paths[index],0x20000);
    if(!installed) {if(fd==-2)return 0;if(fd<0)return fd;close_file(&fd);return -17;}
    if(fd<0)return fd;
    u64 st[16];i64 v=stat_file(fd,st);
    if(!v&&st[6]!=sound_sizes[index])v=-84;
    u32 done=0;
    while(!v&&done<sound_sizes[index]) {
        i64 n=sc(63,fd,(i64)(scratch+done),sound_sizes[index]-done,0,0,0);
        if(n<=0||(u64)n>sound_sizes[index]-done)v=n<0?n:-5;else done+=(u32)n;
    }
    if(!v&&!equal(scratch,sound_data[index],sound_sizes[index]))v=-84;
    i64 c=close_file(&fd);return v?v:c;
}
static i64 sync_directory(void) {
    i64 fd=op("/usr/share/avsystemsound",0x10000);if(fd<0)return fd;
    i64 v=sc(82,fd,0,0,0,0,0),c=close_file(&fd);return v?v:c;
}
static i64 remove_owned(u32 index) {
    i64 fd=op(paths[index],0x20000);if(fd<0)return fd;
    u64 st[16];i64 v=stat_file(fd,st);
    if(!v&&(st[0]!=owned_dev[index]||st[1]!=owned_ino[index]))v=-116;
    i64 c=close_file(&fd);if(!v)v=c;
    if(!v)v=sc(35,-100,(i64)paths[index],0,0,0,0);
    return v;
}
static i64 create(u32 index) {
    i64 fd=op(paths[index],0x200c1);if(fd<0)return fd;
    out.created|=1U<<index;
    u64 st[16];i64 v=stat_file(fd,st);
    if(!v) {owned_dev[index]=st[0];owned_ino[index]=st[1];}
    if(!v)v=write_all(fd,sound_data[index],sound_sizes[index]);
    if(!v)v=sc(82,fd,0,0,0,0,0);
    i64 c=close_file(&fd);if(!v)v=c;
    if(!v)v=check(index,1);
    return v;
}
__attribute__((visibility("default"))) void _init(void) {
    files_base_init();
    const u8 tag[]="A7SFILE1";for(u32 i=0;i<8;i++)out.magic[i]=tag[i];
    out.version=1;out.euid=report.euid;out.pid=report.pid;
    out.cleanup=report.cleanup;out.model_status=report.status;out.status=report.status;
    if(!out.status&&(report.index!=16||report.euid))out.status=-22;
    u8 request[17];i64 n=-1;int rw_attempted=0;
    if(!out.status) {
        n=read_all("/tmp/jiritsu/a7c2.install.request",request,sizeof(request));
        if(n!=16||!equal(request,(const u8*)"A7SFQ001",8)||*(u32*)(request+12)||*(u32*)(request+8)>2)out.status=-22;
        else out.mode=*(u32*)(request+8);
    }
    if(!out.status) {
        out.phase=1;out.status=mount_state(1);
        for(u32 i=0;i<2&&!out.status;i++)out.status=check(i,out.mode==2);
    }
    if(!out.status&&out.mode) {
        out.phase=2;rw_attempted=1;out.remount=remount(0);out.status=out.remount;
        if(!out.status&&out.mode==1) {
            for(u32 i=0;i<2&&!out.status;i++) {out.phase=3+i;out.status=create(i);}
            if(!out.status)out.status=sync_directory();
            if(out.status) {
                for(u32 j=2;j;j--)if(out.created&(1U<<(j-1))) {
                    i64 v=remove_owned(j-1);if(v&&!out.rollback)out.rollback=v;
                }
                i64 v=sync_directory();if(v&&!out.rollback)out.rollback=v;
            }
        } else if(!out.status) {
            /* Remove the CSV first: even an accidentally retained boot hook
             * then falls back to its native bank before the audio disappears. */
            for(u32 j=2;j&&!out.status;j--) {
                out.phase=5;out.status=check(j-1,1);
                if(!out.status)out.status=sc(35,-100,(i64)paths[j-1],0,0,0,0);
            }
            if(!out.status)out.status=sync_directory();
        }
    }
    if(rw_attempted)out.readonly=remount(1);else out.readonly=mount_state(1);
    if(out.readonly&&!out.status)out.status=out.readonly;
    if(!out.status)out.phase=9;
    i64 fd=op("/tmp/jiritsu/shutter.probe.result",0x241);
    if(fd>=0) {write_all(fd,&out,sizeof(out));sc(82,fd,0,0,0,0,0);close_file(&fd);}
}
