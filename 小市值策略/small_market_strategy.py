'''
筛选出市值介于20-30亿的股票，选取其中市值最小的三只股票，
每天开盘买入，持有五个交易日，然后调仓。
'''

## 初始化函数，设定要操作的股票、基准等等
def initialize(context):
    
    # 设定沪深A股为基准
    set_benchmark('000002.XSHG')
    # True为开启动态复权模式，使用真实价格交易
    set_option('use_real_price', True) 
    
    # 设定成交量比例,成交量不超过总成交量的100%
    set_option('order_volume_ratio', 1)
    
    # 买卖佣金万分之五，最低5元，卖出印花税千分之一
    set_order_cost(OrderCost(open_tax=0, close_tax=0.001, 
                                open_commission=0.0005, close_commission=0.0005,
                                min_commission=5), type='stock')
    
    # 持仓股票数量
    g.stocknum = 10
    # 交易日计时器
    g.days = 0 
    # 调仓频率，一个月调仓一次
    g.refresh_rate = 30
    # 运行函数，每分钟运行一次
    run_daily(trade, 'every_bar')

## 选出小市值股票
def check_stocks(context):
    # 股票市值升序查找，返回前2 * stocknum个最小市值的股票
    q = query(
            valuation.code,
            valuation.market_cap
        ).order_by(
            valuation.market_cap.asc()
        ).limit(2 * g.stocknum)

    # 选出低市值的股票，构成buylist
    df = get_fundamentals(q)
    buylist =list(df['code'])

    # 过滤停牌股票
    buylist = filter_paused_stock(buylist)

    return buylist
  
## 交易函数
def trade(context):
    
    # 调仓日期
    if g.days%g.refresh_rate == 0:

        ## 获取持仓列表
        sell_list = list(context.portfolio.positions.keys())
        # 获取市值最小的股票列表
        buy_list = check_stocks(context)
        
        # 如果持仓股票不在buy_list里面，卖出
        for stock in sell_list:
            if stock not in buy_list:
                order_target_value(stock, 0)
                    
        # 如果有持仓，则卖出
        # if len(sell_list) > 0 :
        #     for stock in sell_list:
        #         order_target_value(stock, 0)

        ## 分配资金
        if len(context.portfolio.positions) < g.stocknum :
            Num = g.stocknum - len(context.portfolio.positions)
            Cash = context.portfolio.cash/Num
        else: 
            Cash = 0
    

        ## 买入股票
        for stock in buy_list:
            # 要买的股票不在自己的持仓中，则买入
            if stock not in context.portfolio.positions.keys():
                order_value(stock, Cash)
            # if len(context.portfolio.positions.keys()) < g.stocknum:
            #     order_value(stock, Cash)

    g.days += 1

# 过滤停牌股票
def filter_paused_stock(stock_list):
    current_data = get_current_data()
    return [stock for stock in stock_list if not current_data[stock].paused]
