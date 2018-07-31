import pandas as pd
import ctypes#弹窗提醒
import tushare as ts
import tushare.stock.indictor as idx
import time
for i in range(240):
    cons=ts.get_apis()
    data = ts.bar('399006', conn=cons, asset='INDEX', start_date='2018-06-15', end_date='2018-07-24',freq='1min')
    #判断是否是给定的压力、支撑等关键点位，是则弹窗提示
    zhishu=data.ix[0,'close']
    if(zhishu<1580)|(zhishu>1645):
        ctypes.windll.user32.MessageBoxA(0, 'warnning', 'hint', 0)


    data=data.sort_index(ascending=True)
    data['date']=data.index
    ls=[]
    for i in range(len(data)):
        ls.append(i)
    data.index=ls
    macd,diff,dea=idx.macd(data,12,26,9,'close')

    #截取diff在dea之下的区段
    macd,diff,dea=idx.macd(data,12,26,9,'close')#取得该区段内的MACD各值
    macd = macd * 2 #行情软件显示的MACD是计算出的2倍
    data['diff2']=diff #给data增加diff列，因diff为保留关键字，所以列名用diff2代替
    data['dea'] = dea  # 给data增加dea列
    df_diff_dea=pd.DataFrame(diff-dea,index=data.index,columns=['diff_dea']) #计算diff-dea差值的DataFrame，用以判断波形是顶背离还是底背离，index同data
    df_diff_dea['date'] = data.date #增加date时间列
    dftemp=df_diff_dea[df_diff_dea.diff_dea>0] #diff-dea>0 则diff在dea上，用于判断顶背离
    dftemp2=df_diff_dea[df_diff_dea.diff_dea<0]#diff-dea<0 则diff在dea下，用于判断底背离
    #---------------------------------Diff在DEA下面的区段
    dftemp2_down=dftemp2.sort_index(ascending=False) #倒序，从后往前
    ls=dftemp2_down.index.tolist() #转成列表，比较不连续段，不连续段用于分割2个不同的底背离
    ls_dbl=[] #用于保存底背离区段的index
    down_id_end=0 #diff在dea之下的起始位置
    for i in range(len(ls)-1):#找出不连续Diff在DEA下面的开始位置
        if ((ls[i]-ls[i+1])>1): #比较相邻的2个index是否连续，不连续则是分隔点
            #print('------------------')
            #print(dftemp2_down.iloc[i].date)
            #print(ls[i])  #分割点起始位置
            #print(dftemp2_down.iloc[down_id_end].date)
            #print(ls[down_id_end]) #分隔结束位置
            #print('------------------')
            ls_dbl.append([ls[i], ls[down_id_end]])
            down_id_end=i+1 #上一个波段结束位置为上面循环i-1
    dbl1_diff_min=data[ls_dbl[0][0]:ls_dbl[0][1]+1].diff2.min()
    dbl1_low_min=data[ls_dbl[0][0]:ls_dbl[0][1]+1].low.min()
    dbl2_diff_min=data[ls_dbl[1][0]:ls_dbl[1][1]+1].diff2.min()
    dbl2_low_min=data[ls_dbl[1][0]:ls_dbl[1][1]+1].low.min()

    #-------------------------------Diff位于DEA上面的区段
    dftemp_up=dftemp.sort_index(ascending=False) #倒序，从后往前
    ls_up=dftemp_up.index.tolist() #转成列表，比较不连续段，不连续段用于分割2个不同的底背离
    ls_up_dbl=[] #用于保存底背离区段的index
    up_id_end=0 #diff在dea之下的起始位置
    for i in range(len(ls_up)-1):#找出不连续Diff在DEA下面的开始位置
        if ((ls_up[i]-ls_up[i+1])>1): #比较相邻的2个index是否连续，不连续则是分隔点
            #print('------------------')
            #print(dftemp_up.iloc[i].date)
            #print(ls_up[i])  #分割点起始位置
            #print(dftemp_up.iloc[up_id_end].date)
            #print(ls_up[up_id_end]) #分隔结束位置
            #print('------------------')
            ls_up_dbl.append([ls_up[i], ls_up[up_id_end]])
            up_id_end=i+1 #上一个波段结束位置为上面循环i-1
    dbl1_up_diff_max=data[ls_up_dbl[0][0]:ls_up_dbl[0][1]+1].diff2.max()
    dbl1_up_high_max=data[ls_up_dbl[0][0]:ls_up_dbl[0][1]+1].high.max()

    dbl2_up_diff_max=data[ls_up_dbl[1][0]:ls_up_dbl[1][1]+1].diff2.max()
    dbl2_up_high_max=data[ls_up_dbl[1][0]:ls_up_dbl[1][1]+1].high.max()
    if(dbl1_up_high_max>dbl1_up_high_max)&(dbl1_up_diff_max<dbl2_up_diff_max):
        ctypes.windll.user32.MessageBoxA(0,'top','hint',0)

    #取当日指数数据段
    #data=data[data['date']>=datetime.datetime(2018,7,16,9,30,0)]

    if(dbl2_low_min>dbl1_low_min)&(dbl2_diff_min<dbl1_diff_min):
        ctypes.windll.user32.MessageBoxA(0,'bottom','hint',0)
    time.sleep(60)