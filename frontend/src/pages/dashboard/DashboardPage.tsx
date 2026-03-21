import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  TeamOutlined,
  FileTextOutlined,
  BellOutlined,
  DashboardOutlined,
  PlusOutlined,
  ClockCircleOutlined,
  PhoneOutlined,
  CheckCircleOutlined,
} from '@ant-design/icons'
import { useAuthStore } from '../../stores/authStore'
import styles from './DashboardPage.module.css'

interface DashboardStats {
  totalCustomers: number
  newCustomersToday: number
  pendingFollowups: number
  todayReminders: number
  convertedThisMonth: number
}

interface RecentActivity {
  id: number
  type: 'customer' | 'followup' | 'reminder'
  title: string
  time: string
}

export default function DashboardPage() {
  const navigate = useNavigate()
  const { user, accessToken } = useAuthStore()
  const [stats, setStats] = useState<DashboardStats>({
    totalCustomers: 0,
    newCustomersToday: 0,
    pendingFollowups: 0,
    todayReminders: 0,
    convertedThisMonth: 0,
  })
  const [activities, setActivities] = useState<RecentActivity[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchDashboardData()
  }, [])

  const fetchDashboardData = async () => {
    setLoading(true)
    try {
      // Fetch customers count
      const customersRes = await fetch('/api/v1/customers?page=1&page_size=1', {
        headers: { Authorization: `Bearer ${accessToken}` },
      })
      if (customersRes.ok) {
        const data = await customersRes.json()
        setStats(prev => ({ ...prev, totalCustomers: data.total }))
      }

      // Fetch reminders count
      const remindersRes = await fetch('/api/v1/reminders?page=1&page_size=1&status=pending', {
        headers: { Authorization: `Bearer ${accessToken}` },
      })
      if (remindersRes.ok) {
        const data = await remindersRes.json()
        setStats(prev => ({ ...prev, pendingFollowups: data.total }))
      }

      // Mock recent activities (in real app, fetch from API)
      setActivities([
        { id: 1, type: 'customer', title: '新客户 "张三" 已创建', time: '5分钟前' },
        { id: 2, type: 'followup', title: '完成了客户 "李四" 的跟进', time: '30分钟前' },
        { id: 3, type: 'reminder', title: '服务提醒：王五 - 续费跟进', time: '1小时前' },
        { id: 4, type: 'customer', title: '客户 "赵六" 状态更新为已转化', time: '2小时前' },
      ])
    } catch (error) {
      console.error('Failed to fetch dashboard data:', error)
    } finally {
      setLoading(false)
    }
  }

  const getGreeting = () => {
    const hour = new Date().getHours()
    if (hour < 12) return '早上好'
    if (hour < 18) return '下午好'
    return '晚上好'
  }

  const quickActions = [
    { icon: <PlusOutlined />, label: '新建客户', path: '/customers' },
    { icon: <PhoneOutlined />, label: '添加跟进', path: '/followups' },
    { icon: <BellOutlined />, label: '创建提醒', path: '/reminders' },
    { icon: <DashboardOutlined />, label: '销售机会', path: '/opportunities' },
  ]

  const getActivityIcon = (type: string) => {
    switch (type) {
      case 'customer':
        return <TeamOutlined />
      case 'followup':
        return <FileTextOutlined />
      case 'reminder':
        return <BellOutlined />
      default:
        return <ClockCircleOutlined />
    }
  }

  const getActivityIconStyle = (type: string) => {
    switch (type) {
      case 'customer':
        return { background: '#eff6ff', color: '#2563eb' }
      case 'followup':
        return { background: '#f0fdf4', color: '#16a34a' }
      case 'reminder':
        return { background: '#fef3c7', color: '#d97706' }
      default:
        return { background: '#f1f5f9', color: '#64748b' }
    }
  }

  return (
    <div className={styles.container}>
      {/* Welcome Section */}
      <div className={styles.welcome}>
        <h1 className={styles.welcomeTitle}>{getGreeting()}，{user?.real_name || user?.username} 👋</h1>
        <p className={styles.welcomeSubtitle}>今天是个好日子，开始高效工作吧！</p>
      </div>

      {/* Stats Grid */}
      <div className={styles.statsGrid}>
        <div className={styles.statCard}>
          <div className={`${styles.statIcon} ${styles.statIconBlue}`}>
            <TeamOutlined />
          </div>
          <div className={styles.statValue}>{stats.totalCustomers}</div>
          <div className={styles.statLabel}>总客户数</div>
        </div>

        <div className={styles.statCard}>
          <div className={`${styles.statIcon} ${styles.statIconGreen}`}>
            <CheckCircleOutlined />
          </div>
          <div className={styles.statValue}>{stats.convertedThisMonth}</div>
          <div className={styles.statLabel}>本月转化</div>
        </div>

        <div className={styles.statCard}>
          <div className={`${styles.statIcon} ${styles.statIconOrange}`}>
            <FileTextOutlined />
          </div>
          <div className={styles.statValue}>{stats.pendingFollowups}</div>
          <div className={styles.statLabel}>待跟进</div>
        </div>

        <div className={styles.statCard}>
          <div className={`${styles.statIcon} ${styles.statIconPurple}`}>
            <BellOutlined />
          </div>
          <div className={styles.statValue}>{stats.todayReminders}</div>
          <div className={styles.statLabel}>今日提醒</div>
        </div>
      </div>

      {/* Two Column Layout */}
      <div className={styles.twoColumns}>
        {/* Quick Actions */}
        <div className={styles.quickActions}>
          <h3 className={styles.sectionTitle}>快捷操作</h3>
          <div className={styles.actionGrid}>
            {quickActions.map((action, index) => (
              <div
                key={index}
                className={styles.actionButton}
                onClick={() => navigate(action.path)}
              >
                <div className={styles.actionIcon}>{action.icon}</div>
                <div className={styles.actionLabel}>{action.label}</div>
              </div>
            ))}
          </div>
        </div>

        {/* Recent Activity */}
        <div className={styles.recentActivity}>
          <h3 className={styles.sectionTitle}>最近动态</h3>
          <div className={styles.activityList}>
            {activities.map((activity) => (
              <div key={activity.id} className={styles.activityItem}>
                <div
                  className={styles.activityIcon}
                  style={getActivityIconStyle(activity.type)}
                >
                  {getActivityIcon(activity.type)}
                </div>
                <div className={styles.activityContent}>
                  <div className={styles.activityTitle}>{activity.title}</div>
                  <div className={styles.activityTime}>{activity.time}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
