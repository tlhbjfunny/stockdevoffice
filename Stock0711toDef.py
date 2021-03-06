'''
Ver： 0.02
copyright：Funny
加入对结构成立的判断，并给出当前周期离结构成立的距离
'''
#导入需要的库
import pandas as pd
import numpy as np
import ctypes#弹窗提醒
import tushare as ts
import tushare.stock.indictor as idx

#函数定义
#1.获取上证/深证/创业板股票代码列表
def get_stockcodes(stocktype):  #stocktype 股票类型：sh 上证 sz 深证 cyb 创业板
    if(stocktype=='cyb'): #创业板
        codes=ts.get_gem_classified().code.tolist()
    elif (stocktype=='sz'): #深证
        codes=ts.get_sme_classified().code.tolist()
    elif(stocktype=='sh'): #上证
        codes=ts.get_sz50s().code.tolist() #目前只调用了上证50
    return codes #返回的股票代码列表

#2.顶/底背离判断函数
#def is_devergence(code,start,end,ktype): #code 股票代码，可以是list类型；start 开始时间；end 结束时间 默认当前时间;ketype 周期类型
def get_df_dev(code,start,end,ktype):
    data = ts.get_k_data(code, start, end, ktype)  # 取得周期K线数据
    if (len(data)!=0): #空数据，如停牌股票不计入
        macd,diff,dea=idx.macd(data,12,26,9,'close')#取得该区段内的MACD各值
        macd = macd * 2 #行情软件显示的MACD是计算出的2倍
        data['diff2']=diff #给data增加diff列，因diff为保留关键字，所以列名用diff2代替
        data['dea'] = dea  # 给data增加dea列
        df_diff_dea=pd.DataFrame(diff-dea,index=data.index,columns=['diff_dea']) #计算diff-dea差值的DataFrame，用以判断波形是顶背离还是底背离，index同data
        df_diff_dea['date'] = data.date #增加date时间列
        df_dev_top=df_diff_dea[df_diff_dea.diff_dea>0] #diff-dea>0 则diff在dea上，用于判断顶背离,找出diff在dea之上的区段
        df_dev_bot=df_diff_dea[df_diff_dea.diff_dea<0]#diff-dea<0 则diff在dea下，用于判断底背离，找出diff在dea之下的区段
    return data,df_dev_top,df_dev_bot

#底背离区段id获取函数
def dev_bot(df_dev_bot): #底背离DATa Frame区段
    df_dev_bot=df_dev_bot.sort_index(ascending=False) #diff在dea之下的区段倒序排列，即时间为从后往前
    ls_bot=df_dev_bot.index.tolist() #索引转成列表（索引为整型），比较不连续段，不连续段用于分割2个不同的底背离
    ls_dev_bot=[] #用于保存底背离区段的index
    bot_id_end=0 #diff在dea之下的起始位置
    for i in range(len(ls_bot)-1):#找出不连续Diff在DEA下面的开始位置
        if ((ls_bot[i]-ls_bot[i+1])>3): #比较相邻的2个index是否连续，不连续则是分隔点 *加一对连续区段<=2则视为未交叉的判断,原比较值为1
            ls_dev_bot.append([ls_bot[i], ls_bot[bot_id_end]])
            bot_id_end=i+1 #上一个波段结束位置为上面循环i-1
    return ls_dev_bot #返回底背离区段DataFrame的id 列表 如：[[3,25],[29,35]]
#顶背离区段id获取函数
def dev_top(df_dev_top):
    df_dev_top = df_dev_top.sort_index(ascending=False)  # diff在dea之下的区段倒序排列，即时间为从后往前
    ls_top = df_dev_top.index.tolist()  # 索引转成列表（索引为整型），比较不连续段，不连续段用于分割2个不同的底背离
    ls_dev_top = []  # 用于保存底背离区段的index
    top_id_end = 0  # diff在dea之下的起始位置
    for i in range(len(ls_top) - 1):  # 找出不连续Diff在DEA下面的开始位置
        if ((ls_top[i] - ls_top[i + 1]) > 3):  # 比较相邻的2个index是否连续，不连续则是分隔点 *加一对连续区段<=2则视为未交叉的判断,原比较值为1
            ls_dev_top.append([ls_top[i], ls_top[top_id_end]])
            top_id_end = i + 1  # 上一个波段结束位置为上面循环i-1
    return ls_dev_top #返回顶背离区段id列表

def is_dev(code,start,end,ktype,dev_time): #是否形成底背离判断函数,dev_time默认时间为当前时间
    #判断指定时间节点数据是否存在（未写）

    #根据ktype,对dev_time值进行规整化处理函数（not coding）
    data,df_dev_top,df_dev_bot=get_df_dev(code, start, end, ktype)

    ls_dev_bot=dev_bot(df_dev_bot)
    ls_dev_top=dev_top(df_dev_top)

    # 根据规整化后的dev_time,找出其位于的波段区间list序号
    dev_time_id=data[data.date==dev_time].index #取得指定时间位于data的位置id
    #判断指定时间所处波段类型 识别变量：dev_flag 值：bot:DEA>DIFF top:DEA<DIFF
    dev_flag=''
    if (((data.loc[dev_time_id].dea-data.loc[dev_time_id].diff2)>0).values[0]):
        dev_flag='bot' #dea在diff之上，那么处于调整结构中，前导为死叉，那么接着判断顶背离是否成结构
    elif(((data.loc[dev_time_id].dea-data.loc[dev_time_id].diff2)<0).vlaues[0]):
        dev_flag='top' #dea在diff之下，那么处于预期上涨结构中，前导为金叉，那么接着判断底背离是否成结构
    #根据dev_flag值决定除计算指定时间所处背离种类外，另需计算前导一周期背离种类
    #从而判断结构是否成立
    ls_dev_bot_id = np.NaN
    ls_dev_top_id = np.NaN
    if(len(dev_time_id)!=0): #指定时间节点在data中找到
        if ((data.loc[dev_time_id].diff2.values[0]-data.loc[dev_time_id].dea.values[0])<0):#如果该位置diff位于dea之下则
            for id in ls_dev_bot:
                if dev_time_id in range(id[0],id[1]+1):
                    ls_dev_bot_id=id
            ls_dev_bot_id=ls_dev_bot.index(ls_dev_bot_id)
        else:                                                       #如果该位置diff位于dea之上则
            for id in ls_dev_top:
                if dev_time_id in range(id[0],id[1]+1):
                    ls_dev_top_id=id
            ls_dev_top_id = ls_dev_top.index(ls_dev_top_id)
        #找出该位置是否存在背离
        is_dev_bot=np.NaN
        is_dev_top=np.NaN
        if(len(ls_dev_bot)>=2): #必须有2个以上波段周期才可以判断
            if(~np.isnan(ls_dev_bot_id)): #如果查询时间在Diff小于DEA区段中，判断是否存在底背离
                cur_diff_min = data[ls_dev_bot[ls_dev_bot_id][0]:ls_dev_bot[ls_dev_bot_id][1] + 1].diff2.min() #指定区段diff最低值
                cur_low_min = data[ls_dev_bot[ls_dev_bot_id][0]:ls_dev_bot[ls_dev_bot_id][1] + 1].low.min() #指定区段low最低值
                pre_diff_min = data[ls_dev_bot[ls_dev_bot_id+1][0]:ls_dev_bot[ls_dev_bot_id+1][1] + 1].diff2.min()
                pre_low_min = data[ls_dev_bot[ls_dev_bot_id+1][0]:ls_dev_bot[ls_dev_bot_id+1][1] + 1].low.min()
                if((cur_diff_min>pre_diff_min)&(cur_low_min<pre_low_min)):
                    is_dev_bot=True
        if(len(ls_dev_top)>=2): #必须有2个以上波段周期才可以判断
            if(~np.isnan(ls_dev_top_id)): #如果查询时间在Diff大于DEA区段中，判断是否存在顶背离
                cur_diff_max = data[ls_dev_top[ls_dev_top_id][0]:ls_dev_top[ls_dev_top_id][1] + 1].diff2.max() #指定区段diff最高值
                cur_high_max = data[ls_dev_top[ls_dev_top_id][0]:ls_dev_top[ls_dev_top_id][1] + 1].high.max() #指定区段low最低值
                pre_diff_max = data[ls_dev_top[ls_dev_top_id+1][0]:ls_dev_top[ls_dev_top_id+1][1] + 1].diff2.max()
                pre_high_max = data[ls_dev_top[ls_dev_top_id+1][0]:ls_dev_top[ls_dev_top_id+1][1] + 1].high.max()
                if((cur_diff_max<pre_diff_max)&(cur_high_max>pre_high_max)):
                    is_dev_top=True
    #判断是否成结构

        return data, is_dev_bot, is_dev_top
    else:
        return data,np.NaN,np.NaN








    #背离判断
    #底背离判断

    #顶背离判断

    print(ls_dev_bot)
    print(ls_dev_top)
    return data,ls_dev_bot,ls_dev_top


'''
#测试用

    ls_dev_bot=dev_bot(df_dev_bot)
    ls_dev_top=dev_top(df_dev_top)
    return ls_dev_bot,ls_dev_top

ls_bot,ls_top=is_devergence('300056','2017-01-01','2018-07-27','D')
'''

    #判断相邻2个波谷的Diff、low的值是否形成背离
        if(len(ls_dev_bot)>=2):
            dbl1_diff_min=data[ls_dev_bot[0][0]:ls_dev_bot[0][1]+1].diff2.min()
            dbl1_low_min=data[ls_dev_bot[0][0]:ls_dev_bot[0][1]+1].low.min()

            dbl2_diff_min=data[ls_dev_bot[1][0]:ls_dev_bot[1][1]+1].diff2.min()
            dbl2_low_min=data[ls_dev_bot[1][0]:ls_dev_bot[1][1]+1].low.min()

            if(dbl2_low_min>dbl1_low_min)&(dbl2_diff_min<dbl1_diff_min)&(data.iloc[-1].diff2>dbl1_diff_min)&(abs(data.iloc[-1].dea-data.iloc[-1].diff2)<0.1): #背离且最新diff高于低点diff，即有反身向上趋势
                codes_dbl.append(code)


codes=get_stockcodes('cyb')
print(codes)