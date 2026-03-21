import { useState, useEffect } from 'react'
import { Table, Card, Space, Select, DatePicker, Button, Tag, Drawer, Descriptions, Statistic, Row, Col, message, Input } from 'antd'
import { SearchOutlined, ReloadOutlined } from '@ant-design/icons'
import type { ColumnsType } from 'antd/es/table'
import dayjs from 'dayjs'
import { useAuthStore } from '../../stores/authStore'
import styles from './AuditLogPage.module.css'

const { RangePicker } = DatePicker

interface AuditLog {
  id: number
  actor_user_id: number | null
  actor_name: string | null
  action: string
  resource_type: string
  resource_id: number | null
  before_data: Record<string, any> | null
  after_data: Record<string, any> | null
  ip_address: string | null
  user_agent: string | null
  created_at: string
}

interface AuditLogResponse {
  items: AuditLog[]
  total: number
  page: number
  page_size: number
}

interface AuditLogStats {
  total_logs: number
  action_counts: Record<string, number>
  resource_type_counts: Record<string, number>
}

interface ActionOption {
  value: string
  label: string
}

interface ResourceTypeOption {
  value: string
  label: string
}

const actionLabels: Record<string, string> = {
  create: '创建',
  update: '更新',
  delete: '删除',
  login: '登录',
  logout: '登出',
  export: '导出',
  import: '导入',
  status_change: '状态变更',
}

const resourceTypeLabels: Record<string, string> = {
  customer: '客户',
  user: '用户',
  followup: '跟进记录',
  service_record: '服务记录',
  opportunity: '销售机会',
  reminder: '提醒',
  tag: '标签',
  import_batch: '导入批次',
}

const actionColors: Record<string, string> = {
  create: 'green',
  update: 'blue',
  delete: 'red',
  login: 'cyan',
  logout: 'orange',
  export: 'purple',
  import: 'geekblue',
  status_change: 'gold',
}

export default function AuditLogPage() {
  const { accessToken } = useAuthStore()
  const [loading, setLoading] = useState(false)
  const [logs, setLogs] = useState<AuditLog[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(20)
  const [stats, setStats] = useState<AuditLogStats | null>(null)
  const [actions, setActions] = useState<ActionOption[]>([])
  const [resourceTypes, setResourceTypes] = useState<ResourceTypeOption[]>([])

  // Filters
  const [actorUserId, setActorUserId] = useState<number | undefined>()
  const [actionFilter, setActionFilter] = useState<string | undefined>()
  const [resourceTypeFilter, setResourceTypeFilter] = useState<string | undefined>()
  const [dateRange, setDateRange] = useState<[dayjs.Dayjs, dayjs.Dayjs] | null>(null)

  // Drawer
  const [drawerOpen, setDrawerOpen] = useState(false)
  const [selectedLog, setSelectedLog] = useState<AuditLog | null>(null)

  useEffect(() => {
    fetchActions()
    fetchResourceTypes()
    fetchStats()
  }, [])

  useEffect(() => {
    fetchLogs()
  }, [page, pageSize, actionFilter, resourceTypeFilter, dateRange])

  const fetchLogs = async () => {
    setLoading(true)
    try {
      const params = new URLSearchParams({
        page: String(page),
        page_size: String(pageSize),
      })
      if (actorUserId) params.append('actor_user_id', String(actorUserId))
      if (actionFilter) params.append('action', actionFilter)
      if (resourceTypeFilter) params.append('resource_type', resourceTypeFilter)
      if (dateRange) {
        params.append('start_time', dateRange[0].toISOString())
        params.append('end_time', dateRange[1].toISOString())
      }

      const response = await fetch(`/api/v1/audit/logs?${params}`, {
        headers: {
          Authorization: `Bearer ${accessToken}`,
        },
      })

      if (!response.ok) {
        throw new Error('Failed to fetch audit logs')
      }

      const data: AuditLogResponse = await response.json()
      setLogs(data.items)
      setTotal(data.total)
    } catch (error) {
      message.error('获取审计日志失败')
    } finally {
      setLoading(false)
    }
  }

  const fetchStats = async () => {
    try {
      const response = await fetch('/api/v1/audit/stats', {
        headers: {
          Authorization: `Bearer ${accessToken}`,
        },
      })

      if (response.ok) {
        const data: AuditLogStats = await response.json()
        setStats(data)
      }
    } catch (error) {
      console.error('Failed to fetch stats:', error)
    }
  }

  const fetchActions = async () => {
    try {
      const response = await fetch('/api/v1/audit/actions', {
        headers: {
          Authorization: `Bearer ${accessToken}`,
        },
      })

      if (response.ok) {
        const data: ActionOption[] = await response.json()
        setActions(data)
      }
    } catch (error) {
      console.error('Failed to fetch actions:', error)
    }
  }

  const fetchResourceTypes = async () => {
    try {
      const response = await fetch('/api/v1/audit/resource-types', {
        headers: {
          Authorization: `Bearer ${accessToken}`,
        },
      })

      if (response.ok) {
        const data: ResourceTypeOption[] = await response.json()
        setResourceTypes(data)
      }
    } catch (error) {
      console.error('Failed to fetch resource types:', error)
    }
  }

  const handleViewDetail = (log: AuditLog) => {
    setSelectedLog(log)
    setDrawerOpen(true)
  }

  const handleReset = () => {
    setActorUserId(undefined)
    setActionFilter(undefined)
    setResourceTypeFilter(undefined)
    setDateRange(null)
    setPage(1)
  }

  const columns: ColumnsType<AuditLog> = [
    {
      title: 'ID',
      dataIndex: 'id',
      key: 'id',
      width: 80,
    },
    {
      title: '操作人',
      dataIndex: 'actor_name',
      key: 'actor_name',
      width: 120,
      render: (name: string, record) => name || `用户${record.actor_user_id}` || '-',
    },
    {
      title: '操作类型',
      dataIndex: 'action',
      key: 'action',
      width: 100,
      render: (action: string) => (
        <Tag color={actionColors[action] || 'default'}>
          {actionLabels[action] || action}
        </Tag>
      ),
    },
    {
      title: '资源类型',
      dataIndex: 'resource_type',
      key: 'resource_type',
      width: 120,
      render: (type: string) => resourceTypeLabels[type] || type,
    },
    {
      title: '资源ID',
      dataIndex: 'resource_id',
      key: 'resource_id',
      width: 100,
      render: (id: number | null) => id || '-',
    },
    {
      title: 'IP地址',
      dataIndex: 'ip_address',
      key: 'ip_address',
      width: 130,
      render: (ip: string | null) => ip || '-',
    },
    {
      title: '操作时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 180,
      render: (time: string) => dayjs(time).format('YYYY-MM-DD HH:mm:ss'),
    },
    {
      title: '操作',
      key: 'action_btn',
      width: 80,
      render: (_, record) => (
        <Button type="link" size="small" onClick={() => handleViewDetail(record)}>
          详情
        </Button>
      ),
    },
  ]

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <h2>审计日志</h2>
      </div>

      {/* Statistics Cards */}
      {stats && (
        <Card className={styles.statsCard}>
          <Row gutter={24}>
            <Col span={6}>
              <Statistic title="总日志数" value={stats.total_logs} />
            </Col>
            <Col span={6}>
              <Statistic
                title="创建操作"
                value={stats.action_counts['create'] || 0}
                valueStyle={{ color: '#3f8600' }}
              />
            </Col>
            <Col span={6}>
              <Statistic
                title="更新操作"
                value={stats.action_counts['update'] || 0}
                valueStyle={{ color: '#1890ff' }}
              />
            </Col>
            <Col span={6}>
              <Statistic
                title="删除操作"
                value={stats.action_counts['delete'] || 0}
                valueStyle={{ color: '#cf1322' }}
              />
            </Col>
          </Row>
        </Card>
      )}

      {/* Filters */}
      <Card className={styles.filterCard}>
        <Space wrap size="middle">
          <Input
            placeholder="操作人ID"
            type="number"
            value={actorUserId}
            onChange={(e) => setActorUserId(e.target.value ? Number(e.target.value) : undefined)}
            style={{ width: 120 }}
          />
          <Select
            placeholder="操作类型"
            allowClear
            value={actionFilter}
            onChange={setActionFilter}
            options={actions}
            style={{ width: 120 }}
          />
          <Select
            placeholder="资源类型"
            allowClear
            value={resourceTypeFilter}
            onChange={setResourceTypeFilter}
            options={resourceTypes}
            style={{ width: 120 }}
          />
          <RangePicker
            value={dateRange}
            onChange={(dates) => setDateRange(dates as [dayjs.Dayjs, dayjs.Dayjs] | null)}
            showTime
          />
          <Button icon={<SearchOutlined />} type="primary" onClick={() => fetchLogs()}>
            搜索
          </Button>
          <Button icon={<ReloadOutlined />} onClick={handleReset}>
            重置
          </Button>
        </Space>
      </Card>

      {/* Table */}
      <Card className={styles.tableCard}>
        <div className={styles.tableContainer}>
          <Table
            columns={columns}
            dataSource={logs}
            rowKey="id"
            loading={loading}
            scroll={{ x: 'max-content' }}
            pagination={{
              current: page,
              pageSize,
              total,
              showSizeChanger: true,
              showQuickJumper: true,
              showTotal: (total) => `共 ${total} 条`,
              onChange: (p, ps) => {
                setPage(p)
                setPageSize(ps)
              },
            }}
          />
        </div>
      </Card>

      {/* Detail Drawer */}
      <Drawer
        title="审计日志详情"
        placement="right"
        width={600}
        onClose={() => setDrawerOpen(false)}
        open={drawerOpen}
      >
        {selectedLog && (
          <Descriptions column={1} bordered>
            <Descriptions.Item label="日志ID">{selectedLog.id}</Descriptions.Item>
            <Descriptions.Item label="操作人">
              {selectedLog.actor_name || `用户${selectedLog.actor_user_id}` || '-'}
            </Descriptions.Item>
            <Descriptions.Item label="操作类型">
              <Tag color={actionColors[selectedLog.action] || 'default'}>
                {actionLabels[selectedLog.action] || selectedLog.action}
              </Tag>
            </Descriptions.Item>
            <Descriptions.Item label="资源类型">
              {resourceTypeLabels[selectedLog.resource_type] || selectedLog.resource_type}
            </Descriptions.Item>
            <Descriptions.Item label="资源ID">{selectedLog.resource_id || '-'}</Descriptions.Item>
            <Descriptions.Item label="IP地址">{selectedLog.ip_address || '-'}</Descriptions.Item>
            <Descriptions.Item label="User Agent">
              {selectedLog.user_agent || '-'}
            </Descriptions.Item>
            <Descriptions.Item label="操作时间">
              {dayjs(selectedLog.created_at).format('YYYY-MM-DD HH:mm:ss')}
            </Descriptions.Item>
            <Descriptions.Item label="变更前数据">
              <pre className={styles.codeBlock}>
                {selectedLog.before_data
                  ? JSON.stringify(selectedLog.before_data, null, 2)
                  : '-'}
              </pre>
            </Descriptions.Item>
            <Descriptions.Item label="变更后数据">
              <pre className={styles.codeBlock}>
                {selectedLog.after_data
                  ? JSON.stringify(selectedLog.after_data, null, 2)
                  : '-'}
              </pre>
            </Descriptions.Item>
          </Descriptions>
        )}
      </Drawer>
    </div>
  )
}
