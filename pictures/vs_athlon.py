import os
import statistics as st, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
from PIL import Image
import numpy as np
BL="#00949c"; AT="#eb6834"; INK="#1d2b2d"; INK2="#55605f"; MUT="#8a9391"; TEAL="#0e5a61"; SURF="#fcfcfb"; GRID="#e6e8e6"
a1=[934.1,989.2,1030.2,1028.2,1012.5,1010.8,1008.5,967.5,1039.7,1008.5]
b1=[937.4,984.9,1031.6,1019.3,1005.9,None,1008.2,964.1,1033.5,1005.8]
a2=[774.3,934.7,1041.7,994.8,990.2,943.9,1056.8,1007.5,935.7,977.7]
b2=[783.2,935.7,1044.8,1005.3,989.8,949.4,1053.5,1010.3,937.1,982.4]
A=a1+a2; Bv=b1+b2
pairs=[(b,a) for b,a in zip(Bv,A) if b is not None]
d=[b-a for b,a in pairs]
def stats(v): v=[x for x in v if x is not None]; return st.mean(v),st.stdev(v),max(v)-min(v)
plt.rcParams.update({"font.family":"Helvetica Neue","font.size":13})
fig=plt.figure(figsize=(12,8.4),dpi=150,facecolor=SURF)
# banner
ban=Image.open(os.path.expanduser("~/Claude/Developer/rangebook/public/img/rb-banner.png"))
bax=fig.add_axes([0.04,0.865,0.30,0.11]); bax.imshow(ban); bax.axis("off")
fig.text(0.96,0.94,"BLIPR radar chronograph vs Athlon",ha="right",fontsize=22,weight="bold",color=INK)
fig.text(0.96,0.900,"Same 20 shots, both chronographs at once  ·  .38 Special 158 gr from a lever-action rifle",ha="right",fontsize=12.5,color=INK2)
# stat tiles
tiles=[("19 of 20","shots read\n(1 seen, held back as unsure)"),
       (f"{st.mean(d):+.1f} fps","overall vs the Athlon\n(not biased high or low)"),
       (f"±{st.mean([abs(x) for x in d]):.1f} fps",f"typical gap on any one shot\n({100*st.mean([abs(x) for x in d])/st.mean(A):.1f}% of the speed)"),
       ("0","false readings in string 2\n(after the 1.5 s update)")]
for i,(big,small) in enumerate(tiles):
    x=0.04+i*0.235; ax=fig.add_axes([x,0.725,0.215,0.135]); ax.axis("off")
    ax.add_patch(FancyBboxPatch((0.01,0.02),0.98,0.96,boxstyle="round,pad=0,rounding_size=0.08",fc="white",ec=GRID,lw=1.2,transform=ax.transAxes))
    ax.text(0.08,0.66,big,fontsize=24,weight="bold",color=TEAL,transform=ax.transAxes,va="center")
    ax.text(0.08,0.25,small,fontsize=10.5,linespacing=1.3,color=INK2,transform=ax.transAxes,va="center")
# chart
ax=fig.add_axes([0.07,0.26,0.89,0.40]); ax.set_facecolor(SURF)
x=np.arange(20)+np.array([0]*10+[1]*10)*0.8
w=0.38
for i,(b,a) in enumerate(zip(Bv,A)):
    ax.bar(x[i]-w/2-0.01,a,w,color=AT,zorder=3)
    if b is None: ax.text(x[i]+w/2,40,"seen, no speed",rotation=90,ha="center",va="bottom",fontsize=9.5,color=MUT,zorder=4)
    else: ax.bar(x[i]+w/2+0.01,b,w,color=BL,zorder=3)
ax.set_ylim(0,1200); ax.set_yticks(range(0,1201,200)); ax.yaxis.grid(True,color=GRID,lw=1,zorder=0)
ax.set_ylabel("Velocity (fps)",color=INK2)
ax.set_xticks(x); ax.set_xticklabels([f"#{i%10+1}" for i in range(20)],color=INK2,fontsize=11)
for s in ["top","right","left"]: ax.spines[s].set_visible(False)
ax.spines["bottom"].set_color("#b8bdbb"); ax.tick_params(axis="y",colors=INK2,length=0); ax.tick_params(axis="x",length=0)
ax.text(np.mean(x[:10]),1150,"String 1",ha="center",fontsize=13,weight="bold",color=INK)
ax.text(np.mean(x[10:]),1150,"String 2",ha="center",fontsize=13,weight="bold",color=INK)
from matplotlib.patches import Patch
ax.legend(handles=[Patch(color=AT,label="Athlon"),Patch(color=BL,label="BLIPR")],loc="upper right",bbox_to_anchor=(1,1.13),ncol=2,frameon=False,fontsize=12)
# table
tax=fig.add_axes([0.07,0.07,0.89,0.13]); tax.axis("off")
cols=["","Average","SD","ES","Average","SD","ES"]
xs=[0.0,0.26,0.37,0.47,0.62,0.73,0.83]
tax.text(0.43,1.0,"Athlon",color=AT,weight="bold",ha="center",transform=tax.transAxes,fontsize=12.5)
tax.text(0.79,1.0,"BLIPR",color=BL,weight="bold",ha="center",transform=tax.transAxes,fontsize=12.5)
rowsdat=[]
for name,a,b in [("String 1 (BLIPR's 9 reads)",[x for x,y in zip(a1,b1) if y],[y for y in b1 if y]),("String 2",a2,b2)]:
    rowsdat.append([name]+[f"{v:.1f}" for v in stats(a)]+[f"{v:.1f}" for v in stats(b)])
for j,c in enumerate(cols): tax.text(xs[j]+(0.06 if j else 0),0.72,c,color=MUT,fontsize=11,ha="center" if j else "left",transform=tax.transAxes)
for r,row in enumerate(rowsdat):
    for j,c in enumerate(row): tax.text(xs[j]+(0.06 if j else 0),0.42-r*0.3,c,color=INK,fontsize=12.5,ha="center" if j else "left",transform=tax.transAxes)
tax.text(0.0,-0.42,"Handloads from a progressive press, so the wide spread is the ammo, not the chronographs. BLIPR sat beside the muzzle and the Athlon ran\nat the same time with no interference. One more shot (733 fps) was below BLIPR's speed window and isn't shown.",fontsize=10,color=MUT,transform=tax.transAxes)
import os; out=os.path.join(os.path.dirname(os.path.abspath(__file__)),"out","blipr_vs_athlon_2026-11-27.png")
fig.savefig(out,facecolor=SURF); print(out, "diffs",[round(x,1) for x in d])
