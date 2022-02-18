#!/usr/bin/env python
# coding: utf-8

# In[70]:


import pandas as pd
import numpy as np


# In[71]:


import datetime


# In[87]:


#%%读取原始数据

##基金收益率
r_f = pd.read_csv('/Users/hedwigzhao/Documents/兴业实习/课题1/参考数据底稿/基金复权单位净值日增长率_日历日.csv', index_col = 0)
r_f.index = [datetime.datetime.strptime(str(x),"%Y%m%d") for x in r_f.index]

##基金每季度末的二级分类
fund_type_q = pd.read_csv('/Users/hedwigzhao/Documents/兴业实习/课题1/参考数据底稿/四中基金分类_每季末.csv', index_col = 0)
fund_type_q.index = [datetime.datetime.strptime(str(x),"%Y-%m-%d") for x in fund_type_q.index]

##基金列表
df_fund_list = fund_type_q.columns

##基金每季度末的规模（用于剔除规模小于5000万的基金）
fund_asset = pd.read_csv('/Users/hedwigzhao/Documents/兴业实习/课题1/参考数据底稿/基金规模_合计.csv', index_col = 0)   
fund_asset.index = [datetime.datetime.strptime(str(x),"%Y%m%d") for x in fund_asset.index]

##基金成立日与到期日（用于筛选每个季度末已成立且未退市的基金）
setup_date = pd.read_csv('/Users/hedwigzhao/Documents/兴业实习/课题1/参考数据底稿/四种基金成立日与到期日.csv', index_col = 0, )
setup_date2 = setup_date.loc[df_fund_list]
setup_date2['基金成立日'] = [datetime.datetime.strptime(x,"%Y-%m-%d") for x in setup_date2['基金成立日']]
setup_date2['基金到期日'] = [datetime.datetime.strptime(x,"%Y-%m-%d") if x is not np.NaN else datetime.datetime.strptime("3999-12-31","%Y-%m-%d") for x in setup_date2['基金到期日']]


# In[88]:


#设置成3、6、12可以分别设置成季度、半年度、年度
frequency =  3   
date_list = pd.date_range(start = '20091231',end = '20190930',freq = '%dM'%frequency)


# In[102]:


#收益与滞后规模的关系
l_corr = []
l_corr_s = []
df_size_groupave = pd.DataFrame(columns=date_list)
df_return_groupave = pd.DataFrame(columns=date_list)


for i in range(len(date_list)):
    
    date = date_list[i]
    print('时间点：', date)
    
    ##筛选满足条件的基金列表
    ##先找出所有已成立、未到期的基金
    setup_date3 = setup_date2[setup_date2['基金成立日'] < date]
    setup_date4 = setup_date3[setup_date3['基金到期日'] > date]    
    fund_list = setup_date4.index
    
    ##剔除二级分类不是偏股混合或普通股票型的基金
    fund_type_q_2 = pd.DataFrame(fund_type_q.values.T, index=fund_type_q.columns, columns=fund_type_q.index)                      
    fund_type_q_3 = fund_type_q_2.reindex(fund_list)
    fund_type_q_4 = fund_type_q_3[(fund_type_q_3[date]=='偏股混合型基金')|(fund_type_q_3[date]=='普通股票型基金')|(fund_type_q_3[date]=='灵活配置型基金')|(fund_type_q_3[date]=='平衡混合型基金')]
    fund_list = fund_type_q_4.index
    
    ##剔除规模小于5000万的基金
    fund_asset_2 = pd.DataFrame(fund_asset.values.T, index=fund_asset.columns, columns=fund_asset.index)
    fund_asset_2 = fund_asset_2.reindex(fund_list)
    fund_asset_3 = fund_asset_2[fund_asset_2[date] > 50000000]
    fund_list = fund_asset_3.index
    
    ##基金规模
    size = fund_asset_3[date]
    
    
    ##计算区间累计收益率
    r_f_2 = r_f[r_f.index > date]

    if i == len(date_list)-1:
        r_f_3 = r_f_2[r_f_2.index <= datetime.datetime.strptime('2019-12-31',"%Y-%m-%d")]
    else:
        r_f_3 = r_f_2[r_f_2.index <= date_list[i+1]]
        
    r_f_4 = pd.DataFrame(r_f_3.values.T, index=r_f_3.columns, columns=r_f_3.index)
    r_f_5 = r_f_4.reindex(fund_list)
    
    ret_a_size = pd.DataFrame(index=fund_list)
    for code in fund_list:
        ret_i=1
        for date in r_f_5.columns:
            ret_i *= (1+r_f_5.loc[code,date])

        ret_a_size.loc[code,'ret'] = ret_i
        
        
    ##计算相关系数和矩相关系数  
    ret_a_size['size'] = size
    corr = ret_a_size['size'].corr(ret_a_size['ret'])
    corr_2 = ret_a_size.corr(method='spearman')
    l_corr.append(corr)
    l_corr_s.append(corr_2)
    
    
    ##排序分组，并计算每组规模和收益的均值
    n_port = 5  # portfolio 的数量可以调整
    l_percent = []
    for i in range(n_port):
        p = 100 - (100/n_port)*i
        l_percent.append(p)
        
    l_size = []
    l_return = []
    for p in l_percent:
        highpercentile = np.percentile(ret_a_size['size'], p)
        lowpercentile = np.percentile(ret_a_size['size'], p-100/n_port)
        df_p = ret_a_size[(highpercentile >= ret_a_size['size'])&(ret_a_size['size'] >= lowpercentile)]
        if len(df_p['size']) == 0:
            l_size.append(0)
            l_return.append(0)
        else:
            l_size.append(sum(df_p['size'])/len(df_p['size']))
            l_return.append(sum(df_p['ret'])/len(df_p['ret']))
                 
    
    df_size_groupave[date]=l_size
    df_return_groupave[date]=l_return


# In[103]:


#相关系数和矩相关系数表
corr_df = pd.DataFrame(data = [l_corr,l_corr_s],columns=date_list,index=['相关系数','秩相关系数'])


# In[104]:


corr_df


# In[105]:


#每组规模的的平均值
df_size_groupave


# In[106]:


#每组收益率的平均值
df_return_groupave


# In[107]:


#收益与未来一期规模的关系
l_corr2 = []
l_corr_s2 = []
df_size_groupave2 = pd.DataFrame(columns=date_list)
df_return_groupave2 = pd.DataFrame(columns=date_list)


for i in range(1,len(date_list)):
    
    date = date_list[i]
    print('时间点：', date)
    
    ##筛选满足条件的基金列表
    ##先找出所有已成立、未到期的基金
    setup_date3 = setup_date2[setup_date2['基金成立日'] < date]
    setup_date4 = setup_date3[setup_date3['基金到期日'] > date]    
    fund_list = setup_date4.index
    
    ##剔除二级分类不是偏股混合或普通股票型的基金
    fund_type_q_2 = pd.DataFrame(fund_type_q.values.T, index=fund_type_q.columns, columns=fund_type_q.index)                      
    fund_type_q_3 = fund_type_q_2.reindex(fund_list)
    fund_type_q_4 = fund_type_q_3[(fund_type_q_3[date]=='偏股混合型基金')|(fund_type_q_3[date]=='普通股票型基金')|(fund_type_q_3[date]=='灵活配置型基金')|(fund_type_q_3[date]=='平衡混合型基金')]
    fund_list = fund_type_q_4.index
    
    ##剔除规模小于5000万的基金
    fund_asset_2 = pd.DataFrame(fund_asset.values.T, index=fund_asset.columns, columns=fund_asset.index)
    fund_asset_2 = fund_asset_2.reindex(fund_list)
    fund_asset_3 = fund_asset_2[fund_asset_2[date] > 50000000]
    fund_list = fund_asset_3.index
    
    ##基金规模
    size = fund_asset_3[date]
    
    
    ##计算区间累计收益率
    r_f_2 = r_f[r_f.index < date]
    r_f_3 = r_f_2[r_f_2.index >= date_list[i-1]]
        
    r_f_4 = pd.DataFrame(r_f_3.values.T, index=r_f_3.columns, columns=r_f_3.index)
    r_f_5 = r_f_4.reindex(fund_list)
    
    ret_a_size = pd.DataFrame(index=fund_list)
    for code in fund_list:
        ret_i=1
        for date in r_f_5.columns:
            ret_i *= (1+r_f_5.loc[code,date])

        ret_a_size.loc[code,'ret'] = ret_i
        
        
    ##计算相关系数和矩相关系数  
    ret_a_size['size'] = size
    corr = ret_a_size['size'].corr(ret_a_size['ret'])
    corr_2 = ret_a_size.corr(method='spearman')
    l_corr2.append(corr)
    l_corr_s2.append(corr_2)
    
    
    ##排序分组，并计算每组规模和收益的均值
    n_port = 5  # portfolio 的数量可以调整
    l_percent = []
    for i in range(n_port):
        p = 100 - (100/n_port)*i
        l_percent.append(p)
        
    l_size = []
    l_return = []
    for p in l_percent:
        highpercentile = np.percentile(ret_a_size['size'], p)
        lowpercentile = np.percentile(ret_a_size['size'], p-100/n_port)
        df_p = ret_a_size[(highpercentile >= ret_a_size['size'])&(ret_a_size['size'] >= lowpercentile)]
        if len(df_p['size']) == 0:
            l_size.append(0)
            l_return.append(0)
        else:
            l_size.append(sum(df_p['size'])/len(df_p['size']))
            l_return.append(sum(df_p['ret'])/len(df_p['ret']))
                 
    
    df_size_groupave2[date]=l_size
    df_return_groupave2[date]=l_return


# In[108]:


#相关系数和矩相关系数表
corr_df = pd.DataFrame(data = [l_corr,l_corr_s],columns=date_list,index=['相关系数','秩相关系数'])
corr_df


# In[109]:


#每组规模的的平均值
df_size_groupave


# In[110]:


#每组收益率的平均值
df_return_groupave


# In[ ]:




