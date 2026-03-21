import { useState, useEffect } from 'react'
import { Table, Button, Space, Input, Select, Tag, Modal, Form, message, DatePicker, InputNumber, Card, Dropdown, Popconfirm } from 'antd'
import { PlusOutlined, AppstoreOutlined, UnorderedListOutlined, MoreOutlined } from '@ant-design/icons'
import type { ColumnsType } from 'antd/es/table'
import { useAuthStore } from '../../stores/authStore'
import styles from '../customers/CustomerListPage.module.css'

interface Opportunity {
  id: number
  customer_id: number
  customer_name: string | null
  opportunity_name: string
  expected_amount: number
  probability: number | null
  stage: string
  stage_label: string
  expected_close_date: string | null
  owner_user_id: number
  owner_name: string | null
  created_at: string
  updated_at: string
}

interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  page_size: number
}

interface KanbanResponse {
  columns: Record<string, Opportunity[]>
}

const STAGE_ORDER = ['new', 'qualified', 'proposal', 'negotiation', 'won', 'lost']

const STAGE_LABELS: Record<string, string> = {
  new: '新建',
  qualified: '已验证',
  proposal: '报价',
  negotiation: '谈判',
  won: '赢单',
  lost: '输单',
}

const STAGE_COLORS: Record<string, string> = {
  new: 'blue',
  qualified: 'cyan',
  proposal: 'orange',
  negotiation: 'purple',
  won: 'green',
  lost: 'red',
}

export default function OpportunityListPage() {
  const { accessToken, user } = useAuthStore()
  const [loading, setLoading] = useState(false)
  const [opportunities, setOpportunities] = useState<Opportunity[]>([])
  const [kanbanData, setKanbanData] = useState<Record<string, Opportunity[]>>({})
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(20)
  const [customerFilter, setCustomerFilter] = useState<number | undefined>()
  const [stageFilter, setStageFilter] = useState<string | undefined>()
  const [viewMode, setViewMode] = useState<'table' | 'kanban'>('kanban')
  const [createModalOpen, setCreateModalOpen] = useState(false)
  const [editModalOpen, setEditModalOpen] = useState(false)
  const [editingOpportunity, setEditingOpportunity] = useState<Opportunity | null>(null)
  const [form] = Form.useForm()
  const [customers, setCustomers] = useState<Array<{ id: number; name: string }>>([])

  const fetchOpportunities = async () => {
    setLoading(true)
    try {
      const params = new URLSearchParams({
        page: String(page),
        page_size: String(pageSize),
      })
      if (customerFilter) params.append('customer_id', String(customerFilter))
      if (stageFilter) params.append('stage', stageFilter)

      const response = await fetch(`/api/v1/opportunities?${params}`, {
        headers: { Authorization: `Bearer ${accessToken}` },
      })

      if (!response.ok) throw new Error('Failed to fetch')

      const data: PaginatedResponse<Opportunity> = await response.json()
      setOpportunities(data.items)
      setTotal(data.total)
    } catch (error) {
      message.error('获取销售机会失败')
    } finally {
      setLoading(false)
    }
  }

  const fetchKanbanData = async () => {
    setLoading(true)
    try {
      const params = new URLSearchParams()
      if (customerFilter) params.append('customer_id', String(customerFilter))

      const response = await fetch(`/api/v1/opportunities/kanban?${params}`, {
        headers: { Authorization: `Bearer ${accessToken}` },
      })

      if (!response.ok) throw new Error('Failed to fetch')

      const data: KanbanResponse = await response.json()
      setKanbanData(data.columns)
    } catch (error) {
      message.error('获取看板数据失败')
    } finally {
      setLoading(false)
    }
  }

  const fetchCustomers = async () => {
    try {
      const response = await fetch('/api/v1/customers?page=1&page_size=100', {
        headers: { Authorization: `Bearer ${accessToken}` },
      })
      if (response.ok) {
        const data = await response.json()
        setCustomers(data.items.map((c: any) => ({ id: c.id, name: c.name })))
      }
    } catch (error) {
      console.error('Failed to fetch customers:', error)
    }
  }

  useEffect(() => {
    if (viewMode === 'table') {
      fetchOpportunities()
    } else {
      fetchKanbanData()
    }
  }, [page, pageSize, customerFilter, stageFilter, viewMode])

  useEffect(() => {
    fetchCustomers()
  }, [])

  const handleCreate = async (values: any) => {
    try {
      const response = await fetch('/api/v1/opportunities', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${accessToken}`,
        },
        body: JSON.stringify({
          ...values,
          expected_close_date: values.expected_close_date?.format('YYYY-MM-DD'),
        }),
      })

      if (!response.ok) {
        const error = await response.json()
        message.error(error.detail || '创建失败')
        return
      }

      message.success('创建成功')
      setCreateModalOpen(false)
      form.resetFields()
      if (viewMode === 'table') {
        fetchOpportunities()
      } else {
        fetchKanbanData()
      }
    } catch (error) {
      message.error('创建失败')
    }
  }

  const handleUpdate = async (values: any) => {
    if (!editingOpportunity) return

    try {
      const response = await fetch(`/api/v1/opportunities/${editingOpportunity.id}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${accessToken}`,
        },
        body: JSON.stringify({
          ...values,
          expected_close_date: values.expected_close_date?.format('YYYY-MM-DD'),
        }),
      })

      if (!response.ok) {
        const error = await response.json()
        message.error(error.detail || '更新失败')
        return
      }

      message.success('更新成功')
      setEditModalOpen(false)
      setEditingOpportunity(null)
      form.resetFields()
      if (viewMode === 'table') {
        fetchOpportunities()
      } else {
        fetchKanbanData()
      }
    } catch (error) {
      message.error('更新失败')
    }
  }

  const handleDelete = async (id: number) => {
    try {
      const response = await fetch(`/api/v1/opportunities/${id}`, {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${accessToken}` },
      })

      if (!response.ok) {
        message.error('删除失败')
        return
      }

      message.success('删除成功')
      if (viewMode === 'table') {
        fetchOpportunities()
      } else {
        fetchKanbanData()
      }
    } catch (error) {
      message.error('删除失败')
    }
  }

  const handleStageChange = async (id: number, newStage: string) => {
    try {
      const response = await fetch(`/api/v1/opportunities/${id}/stage`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${accessToken}`,
        },
        body: JSON.stringify({ stage: newStage }),
      })

      if (!response.ok) {
        message.error('更新阶段失败')
        return
      }

      message.success('阶段更新成功')
      if (viewMode === 'table') {
        fetchOpportunities()
      } else {
        fetchKanbanData()
      }
    } catch (error) {
      message.error('更新阶段失败')
    }
  }

  const openEditModal = (opportunity: Opportunity) => {
    setEditingOpportunity(opportunity)
    form.setFieldsValue({
      opportunity_name: opportunity.opportunity_name,
      expected_amount: opportunity.expected_amount,
      probability: opportunity.probability,
      stage: opportunity.stage,
      expected_close_date: opportunity.expected_close_date ? dayjs(opportunity.expected_close_date) : null,
    })
    setEditModalOpen(true)
  }

  const columns: ColumnsType<Opportunity> = [
    {
      title: '机会名称',
      dataIndex: 'opportunity_name',
      key: 'opportunity_name',
      width: 200,
    },
    {
      title: '客户',
      dataIndex: 'customer_name',
      key: 'customer_name',
      width: 150,
      render: (text) => text || '-',
    },
    {
      title: '阶段',
      dataIndex: 'stage',
      key: 'stage',
      width: 100,
      render: (stage) => (
        <Tag color={STAGE_COLORS[stage] || 'default'}>
          {STAGE_LABELS[stage] || stage}
        </Tag>
      ),
    },
    {
      title: '预期金额',
      dataIndex: 'expected_amount',
      key: 'expected_amount',
      width: 120,
      render: (amount) => amount ? `¥${Number(amount).toLocaleString()}` : '-',
    },
    {
      title: '概率',
      dataIndex: 'probability',
      key: 'probability',
      width: 80,
      render: (prob) => prob ? `${prob}%` : '-',
    },
    {
      title: '预计成交日期',
      dataIndex: 'expected_close_date',
      key: 'expected_close_date',
      width: 120,
      render: (date) => date || '-',
    },
    {
      title: '负责人',
      dataIndex: 'owner_name',
      key: 'owner_name',
      width: 100,
      render: (text) => text || '-',
    },
    {
      title: '操作',
      key: 'action',
      width: 150,
      render: (_, record) => (
        <Space>
          <Button type="link" size="small" onClick={() => openEditModal(record)}>
            编辑
          </Button>
          <Dropdown
            menu={{
              items: STAGE_ORDER.filter(s => s !== record.stage).map(s => ({
                key: s,
                label: `移至 ${STAGE_LABELS[s]}`,
              })),
              onClick: ({ key }) => handleStageChange(record.id, key),
            }}
          >
            <Button type="link" size="small">改阶段</Button>
          </Dropdown>
          <Popconfirm
            title="确定删除此销售机会?"
            onConfirm={() => handleDelete(record.id)}
            okText="确定"
            cancelText="取消"
          >
            <Button type="link" size="small" danger>删除</Button>
          </Popconfirm>
        </Space>
      ),
    },
  ]

  const renderKanbanColumn = (stage: string, opportunities: Opportunity[]) => (
    <div key={stage} style={{ minWidth: 280, width: 280, flexShrink: 0 }}>
      <div style={{
        background: '#f5f5f5',
        padding: '12px 16px',
        borderRadius: '8px 8px 0 0',
        borderBottom: `3px solid ${STAGE_COLORS[stage] === 'green' ? '#52c41a' : STAGE_COLORS[stage] === 'red' ? '#ff4d4f' : '#1890ff'}`,
      }}>
        <Space>
          <Tag color={STAGE_COLORS[stage]}>{STAGE_LABELS[stage]}</Tag>
          <span style={{ color: '#666' }}>{opportunities.length}</span>
        </Space>
      </div>
      <div style={{
        background: '#fafafa',
        padding: '12px',
        borderRadius: '0 0 8px 8px',
        minHeight: 400,
        maxHeight: 'calc(100vh - 280px)',
        overflowY: 'auto',
      }}>
        {opportunities.map((opp) => (
          <Card
            key={opp.id}
            size="small"
            style={{ marginBottom: 12 }}
            actions={[
              <Dropdown
                key="stage"
                menu={{
                  items: STAGE_ORDER.filter(s => s !== opp.stage).map(s => ({
                    key: s,
                    label: `移至 ${STAGE_LABELS[s]}`,
                  })),
                  onClick: ({ key }) => handleStageChange(opp.id, key),
                }}
              >
                <Button type="text" size="small">改阶段</Button>
              </Dropdown>,
              <Button key="edit" type="text" size="small" onClick={() => openEditModal(opp)}>编辑</Button>,
              <Popconfirm
                key="delete"
                title="确定删除?"
                onConfirm={() => handleDelete(opp.id)}
                okText="确定"
                cancelText="取消"
              >
                <Button type="text" size="small" danger>删除</Button>
              </Popconfirm>,
            ]}
          >
            <Card.Meta
              title={opp.opportunity_name}
              description={
                <div>
                  <div style={{ marginBottom: 8 }}>
                    <span style={{ color: '#666' }}>客户: </span>
                    {opp.customer_name || '-'}
                  </div>
                  <div style={{ marginBottom: 8 }}>
                    <span style={{ color: '#666' }}>金额: </span>
                    <span style={{ fontWeight: 'bold', color: '#1890ff' }}>
                      ¥{Number(opp.expected_amount).toLocaleString()}
                    </span>
                  </div>
                  <div style={{ marginBottom: 8 }}>
                    <span style={{ color: '#666' }}>概率: </span>
                    {opp.probability ? `${opp.probability}%` : '-'}
                  </div>
                  <div>
                    <span style={{ color: '#666' }}>成交日期: </span>
                    {opp.expected_close_date || '-'}
                  </div>
                </div>
              }
            />
          </Card>
        ))}
        {opportunities.length === 0 && (
          <div style={{ textAlign: 'center', color: '#999', padding: 20 }}>
            暂无数据
          </div>
        )}
      </div>
    </div>
  )

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <h2>销售机会</h2>
        <Space>
          <Button
            icon={viewMode === 'kanban' ? <UnorderedListOutlined /> : <AppstoreOutlined />}
            onClick={() => setViewMode(viewMode === 'kanban' ? 'table' : 'kanban')}
          >
            {viewMode === 'kanban' ? '列表视图' : '看板视图'}
          </Button>
          <Button type="primary" icon={<PlusOutlined />} onClick={() => setCreateModalOpen(true)}>
            新建机会
          </Button>
        </Space>
      </div>

      <div className={styles.filters}>
        <Space>
          <Select
            placeholder="筛选客户"
            value={customerFilter}
            onChange={setCustomerFilter}
            allowClear
            showSearch
            optionFilterProp="label"
            style={{ width: 200 }}
            options={customers.map(c => ({ value: c.id, label: c.name }))}
          />
          {viewMode === 'table' && (
            <Select
              placeholder="筛选阶段"
              value={stageFilter}
              onChange={setStageFilter}
              allowClear
              style={{ width: 150 }}
              options={Object.entries(STAGE_LABELS).map(([value, label]) => ({ value, label }))}
            />
          )}
        </Space>
      </div>

      {viewMode === 'table' ? (
        <div className={styles.tableContainer}>
          <Table
            columns={columns}
            dataSource={opportunities}
            rowKey="id"
            loading={loading}
            scroll={{ x: 'max-content' }}
            pagination={{
              current: page,
              pageSize,
              total,
              showSizeChanger: true,
              showTotal: (total) => `共 ${total} 条`,
              onChange: (p, ps) => { setPage(p); setPageSize(ps); },
            }}
          />
        </div>
      ) : (
        <div style={{ display: 'flex', gap: 16, overflowX: 'auto', paddingBottom: 16 }}>
          {STAGE_ORDER.map(stage => renderKanbanColumn(stage, kanbanData[stage] || []))}
        </div>
      )}

      <Modal
        title="新建销售机会"
        open={createModalOpen}
        onCancel={() => setCreateModalOpen(false)}
        footer={null}
        width={600}
      >
        <Form form={form} layout="vertical" onFinish={handleCreate}>
          <Form.Item name="customer_id" label="客户" rules={[{ required: true, message: '请选择客户' }]}>
            <Select
              showSearch
              optionFilterProp="label"
              options={customers.map(c => ({ value: c.id, label: c.name }))}
            />
          </Form.Item>
          <Form.Item name="opportunity_name" label="机会名称" rules={[{ required: true, message: '请输入机会名称' }]}>
            <Input />
          </Form.Item>
          <Form.Item name="expected_amount" label="预期金额">
            <InputNumber
              style={{ width: '100%' }}
              min={0}
              precision={2}
              formatter={value => `¥ ${value}`.replace(/\B(?=(\d{3})+(?!\d))/g, ',')}
              parser={value => value!.replace(/\¥\s?|(,*)/g, '') as any}
            />
          </Form.Item>
          <Form.Item name="probability" label="成交概率(%)">
            <InputNumber style={{ width: '100%' }} min={0} max={100} />
          </Form.Item>
          <Form.Item name="stage" label="阶段" initialValue="new">
            <Select options={Object.entries(STAGE_LABELS).map(([value, label]) => ({ value, label }))} />
          </Form.Item>
          <Form.Item name="expected_close_date" label="预计成交日期">
            <DatePicker style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item>
            <Space>
              <Button type="primary" htmlType="submit">创建</Button>
              <Button onClick={() => setCreateModalOpen(false)}>取消</Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>

      <Modal
        title="编辑销售机会"
        open={editModalOpen}
        onCancel={() => { setEditModalOpen(false); setEditingOpportunity(null); }}
        footer={null}
        width={600}
      >
        <Form form={form} layout="vertical" onFinish={handleUpdate}>
          <Form.Item name="opportunity_name" label="机会名称" rules={[{ required: true, message: '请输入机会名称' }]}>
            <Input />
          </Form.Item>
          <Form.Item name="expected_amount" label="预期金额">
            <InputNumber
              style={{ width: '100%' }}
              min={0}
              precision={2}
              formatter={value => `¥ ${value}`.replace(/\B(?=(\d{3})+(?!\d))/g, ',')}
              parser={value => value!.replace(/\¥\s?|(,*)/g, '') as any}
            />
          </Form.Item>
          <Form.Item name="probability" label="成交概率(%)">
            <InputNumber style={{ width: '100%' }} min={0} max={100} />
          </Form.Item>
          <Form.Item name="stage" label="阶段">
            <Select options={Object.entries(STAGE_LABELS).map(([value, label]) => ({ value, label }))} />
          </Form.Item>
          <Form.Item name="expected_close_date" label="预计成交日期">
            <DatePicker style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item>
            <Space>
              <Button type="primary" htmlType="submit">保存</Button>
              <Button onClick={() => { setEditModalOpen(false); setEditingOpportunity(null); }}>取消</Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}
