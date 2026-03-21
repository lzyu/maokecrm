import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { Card, Descriptions, Tag, Button, Space, Timeline, message, Spin, Empty, Badge, Modal, Form, Input, Select } from 'antd'
import { ArrowLeftOutlined, EditOutlined, PhoneOutlined, MessageOutlined, TeamOutlined, BellOutlined, ShoppingCartOutlined, CalendarOutlined, SolutionOutlined, UserAddOutlined } from '@ant-design/icons'
import dayjs from 'dayjs'
import { useAuthStore } from '../../stores/authStore'
import type { Customer } from '../../api/generated'
import styles from './CustomerDetailPage.module.css'

const statusColors: Record<string, string> = {
  potential: 'default',
  interested: 'blue',
  converted: 'green',
  lost: 'red',
}

const statusLabels: Record<string, string> = {
  potential: '潜在客户',
  interested: '有意向',
  converted: '已转化',
  lost: '已流失',
}

interface TimelineEvent {
  id: number
  event_type: string
  event_type_label: string
  event_time: string
  title: string
  description: string | null
  operator_id: number | null
  operator_name: string | null
  reference_id: number | null
  extra_data: Record<string, any> | null
}

interface TimelineResponse {
  items: TimelineEvent[]
  total: number
  customer_id: number
  customer_name: string
}

// Event type colors and icons
const eventTypeConfig: Record<string, { color: string; icon: React.ReactNode }> = {
  followup: { color: 'blue', icon: <PhoneOutlined /> },
  service_record: { color: 'green', icon: <SolutionOutlined /> },
  opportunity: { color: 'orange', icon: <TeamOutlined /> },
  reminder: { color: 'purple', icon: <BellOutlined /> },
  purchase: { color: 'cyan', icon: <ShoppingCartOutlined /> },
  attendance: { color: 'geekblue', icon: <CalendarOutlined /> },
  consultation: { color: 'magenta', icon: <SolutionOutlined /> },
  customer_created: { color: 'gold', icon: <UserAddOutlined /> },
}

export default function CustomerDetailPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const { user } = useAuthStore()
  const [loading, setLoading] = useState(true)
  const [timelineLoading, setTimelineLoading] = useState(false)
  const [customer, setCustomer] = useState<Customer | null>(null)
  const [timelineEvents, setTimelineEvents] = useState<TimelineEvent[]>([])
  const [timelineTotal, setTimelineTotal] = useState(0)
  const [editModalOpen, setEditModalOpen] = useState(false)
  const [editLoading, setEditLoading] = useState(false)
  const [tags, setTags] = useState<{ id: number; tag_name: string }[]>([])
  const [form] = Form.useForm()

  useEffect(() => {
    fetchCustomer()
    fetchTimeline()
    fetchTags()
  }, [id])

  const fetchTags = async () => {
    try {
      const response = await fetch('/api/v1/tags?skip=0&limit=100', {
        headers: {
          Authorization: `Bearer ${useAuthStore.getState().accessToken}`,
        },
      })
      if (response.ok) {
        const data = await response.json()
        setTags(data.items || [])
      }
    } catch (error) {
      console.error('Failed to fetch tags:', error)
    }
  }

  const fetchCustomer = async () => {
    if (!id) return

    setLoading(true)
    try {
      const response = await fetch(`/api/v1/customers/${id}`, {
        headers: {
          Authorization: `Bearer ${useAuthStore.getState().accessToken}`,
        },
      })

      if (!response.ok) {
        throw new Error('Failed to fetch customer')
      }

      const data = await response.json()
      setCustomer(data)
    } catch (error) {
      message.error('获取客户信息失败')
      navigate('/customers')
    } finally {
      setLoading(false)
    }
  }

  const fetchTimeline = async () => {
    if (!id) return

    setTimelineLoading(true)
    try {
      const response = await fetch(`/api/v1/timeline/${id}`, {
        headers: {
          Authorization: `Bearer ${useAuthStore.getState().accessToken}`,
        },
      })

      if (!response.ok) {
        throw new Error('Failed to fetch timeline')
      }

      const data: TimelineResponse = await response.json()
      setTimelineEvents(data.items)
      setTimelineTotal(data.total)
    } catch (error) {
      console.error('Failed to fetch timeline:', error)
    } finally {
      setTimelineLoading(false)
    }
  }

  const handleEditClick = () => {
    if (customer) {
      form.setFieldsValue({
        name: customer.name,
        phone: customer.phone,
        wechat: customer.wechat,
        company_name: customer.company_name,
        industry: customer.industry,
        source_channel: customer.source_channel,
        customer_status: customer.customer_status,
        tag_ids: customer.tags?.map((t: any) => t.id) || [],
      })
      setEditModalOpen(true)
    }
  }

  const handleEditSubmit = async (values: any) => {
    if (!id) return

    setEditLoading(true)
    try {
      const response = await fetch(`/api/v1/customers/${id}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${useAuthStore.getState().accessToken}`,
        },
        body: JSON.stringify(values),
      })

      if (!response.ok) {
        throw new Error('Failed to update customer')
      }

      message.success('客户信息已更新')
      setEditModalOpen(false)
      fetchCustomer()
    } catch (error) {
      message.error('更新客户信息失败')
    } finally {
      setEditLoading(false)
    }
  }

  const renderTimelineContent = (event: TimelineEvent) => {
    const config = eventTypeConfig[event.event_type] || { color: 'default', icon: null }

    let extraInfo = null
    if (event.extra_data) {
      if (event.event_type === 'followup') {
        const resultLabels: Record<string, string> = {
          no_answer: '未接通',
          contacted: '已联系',
          interested: '有意向',
          rejected: '已拒绝',
          pending: '待跟进',
        }
        extraInfo = event.extra_data.result && (
          <Tag color={event.extra_data.result === 'interested' ? 'green' : 'default'}>
            {resultLabels[event.extra_data.result] || event.extra_data.result}
          </Tag>
        )
      } else if (event.event_type === 'service_record' && event.extra_data.satisfaction_score) {
        extraInfo = <Tag color="gold">满意度: {event.extra_data.satisfaction_score}/5</Tag>
      } else if (event.event_type === 'opportunity') {
        if (event.extra_data.stage) {
          const stageColors: Record<string, string> = {
            new: 'default',
            qualified: 'blue',
            proposal: 'cyan',
            negotiation: 'orange',
            won: 'green',
            lost: 'red',
          }
          extraInfo = (
            <Tag color={stageColors[event.extra_data.stage] || 'default'}>
              {event.extra_data.stage_label || event.extra_data.stage}
            </Tag>
          )
        }
      } else if (event.event_type === 'attendance' && event.extra_data?.status_label) {
        const statusColors: Record<string, string> = {
          attended: 'green',
          absent: 'red',
          leave: 'orange',
        }
        extraInfo = (
          <Tag color={statusColors[event.extra_data.status] || 'default'}>
            {event.extra_data.status_label}
          </Tag>
        )
      }
    }

    return (
      <div className={styles.timelineItem}>
        <div className={styles.timelineHeader}>
          <Space>
            <Tag color={config.color}>{event.event_type_label}</Tag>
            <span className={styles.timelineTitle}>{event.title}</span>
            {extraInfo}
          </Space>
          <span className={styles.timelineTime}>
            {dayjs(event.event_time).format('YYYY-MM-DD HH:mm')}
          </span>
        </div>
        {event.description && (
          <div className={styles.timelineDescription}>{event.description}</div>
        )}
        {event.operator_name && (
          <div className={styles.timelineOperator}>
            操作人: {event.operator_name}
          </div>
        )}
      </div>
    )
  }

  if (loading) {
    return (
      <div className={styles.loading}>
        <Spin size="large" />
      </div>
    )
  }

  if (!customer) {
    return null
  }

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <Space>
          <Button icon={<ArrowLeftOutlined />} onClick={() => navigate('/customers')}>
            返回
          </Button>
          <h2>{customer.name}</h2>
          <Tag color={statusColors[customer.customer_status]}>
            {statusLabels[customer.customer_status] || customer.customer_status}
          </Tag>
        </Space>
        <Button type="primary" icon={<EditOutlined />} onClick={handleEditClick}>
          编辑
        </Button>
      </div>

      <Card title="基本信息" className={styles.card}>
        <Descriptions column={3} bordered>
          <Descriptions.Item label="客户名称">{customer.name}</Descriptions.Item>
          <Descriptions.Item label="手机号">{customer.phone || '-'}</Descriptions.Item>
          <Descriptions.Item label="微信号">{customer.wechat || '-'}</Descriptions.Item>
          <Descriptions.Item label="公司">{customer.company_name || '-'}</Descriptions.Item>
          <Descriptions.Item label="行业">{customer.industry || '-'}</Descriptions.Item>
          <Descriptions.Item label="来源">{customer.source_channel || '-'}</Descriptions.Item>
          <Descriptions.Item label="负责人">{customer.owner_name || '-'}</Descriptions.Item>
          <Descriptions.Item label="标签">
            <Space>
              {customer.tags?.map((tag: any) => (
                <Tag key={tag.id} color="blue">
                  {tag.tag_name || tag.name}
                </Tag>
              ))}
              {(!customer.tags || customer.tags.length === 0) && '-'}
            </Space>
          </Descriptions.Item>
          <Descriptions.Item label="状态">
            <Tag color={statusColors[customer.customer_status]}>
              {statusLabels[customer.customer_status] || customer.customer_status}
            </Tag>
          </Descriptions.Item>
          <Descriptions.Item label="创建时间">
            {dayjs(customer.created_at).format('YYYY-MM-DD HH:mm:ss')}
          </Descriptions.Item>
          <Descriptions.Item label="最后跟进">
            {customer.last_followup_at
              ? dayjs(customer.last_followup_at).format('YYYY-MM-DD HH:mm:ss')
              : '-'}
          </Descriptions.Item>
          <Descriptions.Item label="更新时间">
            {dayjs(customer.updated_at).format('YYYY-MM-DD HH:mm:ss')}
          </Descriptions.Item>
        </Descriptions>
      </Card>

      <Card
        title={
          <Space>
            <span>客户时间线</span>
            <Badge count={timelineTotal} style={{ backgroundColor: '#1890ff' }} />
          </Space>
        }
        className={styles.card}
      >
        {timelineLoading ? (
          <div className={styles.timelineLoading}>
            <Spin />
          </div>
        ) : timelineEvents.length > 0 ? (
          <Timeline
            items={timelineEvents.map((event) => ({
              color: eventTypeConfig[event.event_type]?.color || 'gray',
              dot: eventTypeConfig[event.event_type]?.icon,
              children: renderTimelineContent(event),
            }))}
          />
        ) : (
          <Empty description="暂无时间线记录" />
        )}
      </Card>

      <Modal
        title="编辑客户"
        open={editModalOpen}
        onCancel={() => setEditModalOpen(false)}
        footer={null}
        width={600}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleEditSubmit}
        >
          <Form.Item name="name" label="客户名称" rules={[{ required: true, message: '请输入客户名称' }]}>
            <Input />
          </Form.Item>
          <Form.Item name="phone" label="手机号">
            <Input />
          </Form.Item>
          <Form.Item name="wechat" label="微信号">
            <Input />
          </Form.Item>
          <Form.Item name="company_name" label="公司名称">
            <Input />
          </Form.Item>
          <Form.Item name="industry" label="行业">
            <Input />
          </Form.Item>
          <Form.Item name="source_channel" label="来源渠道">
            <Input />
          </Form.Item>
          <Form.Item name="customer_status" label="客户状态">
            <Select options={Object.entries(statusLabels).map(([value, label]) => ({ value, label }))} />
          </Form.Item>
          <Form.Item name="tag_ids" label="标签">
            <Select
              mode="multiple"
              options={tags.map(t => ({ value: t.id, label: t.tag_name }))}
              placeholder="选择标签"
            />
          </Form.Item>
          <Form.Item>
            <Space>
              <Button type="primary" htmlType="submit" loading={editLoading}>保存</Button>
              <Button onClick={() => setEditModalOpen(false)}>取消</Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}
