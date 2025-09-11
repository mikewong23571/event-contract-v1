'use client';

import Link from 'next/link';
import { motion } from 'framer-motion';
import Dashboard from '@/components/layout/Dashboard';
import { Card, CardContent, CardHeader, Button } from '@/components/ui';
import { PageContainer } from '@/components/ui/PageTransition';
import { staggerContainer, staggerItem } from '@/utils/animations';

export default function HomePage() {
  return (
    <Dashboard currentPage="Home">
      <PageContainer 
        title="Event Contract Trading System"
        subtitle="基于概率的币安事件合约交易信号系统"
        className="space-y-8"
      >
        <motion.div 
          className="grid gap-6 md:grid-cols-2 lg:grid-cols-3"
          variants={staggerContainer}
          initial="initial"
          animate="animate"
        >
          <motion.div variants={staggerItem}>
            <Card variant="elevated" hover className="h-full flex flex-col">
              <CardHeader>
                <div className="flex items-center gap-3 mb-2">
                  <div className="p-2 rounded-lg bg-primary/10">
                    <svg className="h-5 w-5 text-primary" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
                    </svg>
                  </div>
                  <h3 className="text-lg font-semibold text-foreground">交易信号</h3>
                </div>
                <p className="text-muted-foreground text-sm">实时概率交易信号与风险评估</p>
              </CardHeader>
              <CardContent className="flex-1 flex flex-col justify-end">
                <Link href="/signals" className="w-full">
                  <Button variant="primary" className="w-full">查看信号</Button>
                </Link>
              </CardContent>
            </Card>
          </motion.div>

          <motion.div variants={staggerItem}>
            <Card variant="elevated" hover className="h-full flex flex-col">
              <CardHeader>
                <div className="flex items-center gap-3 mb-2">
                  <div className="p-2 rounded-lg bg-secondary/10">
                    <svg className="h-5 w-5 text-secondary" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                    </svg>
                  </div>
                  <h3 className="text-lg font-semibold text-foreground">市场数据</h3>
                </div>
                <p className="text-muted-foreground text-sm">实时K线数据与多时间框架指标</p>
              </CardHeader>
              <CardContent className="flex-1 flex flex-col justify-end">
                <Link href="/market-data" className="w-full">
                  <Button variant="primary" className="w-full">查看数据</Button>
                </Link>
              </CardContent>
            </Card>
          </motion.div>

          <motion.div variants={staggerItem}>
            <Card variant="elevated" hover className="h-full flex flex-col">
              <CardHeader>
                <div className="flex items-center gap-3 mb-2">
                  <div className="p-2 rounded-lg bg-accent/10">
                    <svg className="h-5 w-5 text-accent" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                  </div>
                  <h3 className="text-lg font-semibold text-foreground">回测分析</h3>
                </div>
                <p className="text-muted-foreground text-sm">历史模拟与性能分析</p>
              </CardHeader>
              <CardContent className="flex-1 flex flex-col justify-end">
                <Link href="/backtesting" className="w-full">
                  <Button variant="primary" className="w-full">运行回测</Button>
                </Link>
              </CardContent>
            </Card>
          </motion.div>
        </motion.div>

        <motion.div 
          className="grid gap-6 md:grid-cols-2"
          variants={staggerContainer}
          initial="initial"
          animate="animate"
        >
          <motion.div variants={staggerItem}>
            <Card className="p-4">
              <CardContent className="p-0">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="status-online" />
                    <span className="text-sm font-medium text-foreground">后端 API</span>
                  </div>
                  <Link 
                    href="http://localhost:8000/docs" 
                    target="_blank" 
                    rel="noreferrer" 
                    className="text-sm text-primary hover:text-primary/80 transition-colors"
                  >
                    文档
                  </Link>
                </div>
              </CardContent>
            </Card>
          </motion.div>
          
          <motion.div variants={staggerItem}>
            <Card className="p-4">
              <CardContent className="p-0">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="status-online" />
                    <span className="text-sm font-medium text-foreground">WebSocket</span>
                  </div>
                  <span className="text-sm text-muted-foreground">已连接</span>
                </div>
              </CardContent>
            </Card>
          </motion.div>
        </motion.div>
      </PageContainer>
    </Dashboard>
  );
}
