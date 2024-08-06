import request_handler from '@/api/base'
import { ElMessage } from 'element-plus'
import { ref } from 'vue'

// 调用登录接口数据结构定义
type ProductListType = {
  // accessToken: string // 登录验证 header
  currentPage?: number // 当前页号
  pageSize?: number // 每页记录数
}

interface ProductListItem {
  user_id: string // User 识别号，用于区分不用的用户调用
  request_id: string // 请求 ID，用于生成 TTS & 数字人
  name: string
  heightlight: string
  image_path: string
  instruction_path: string
  departure_place: string
  delivery_company: string
}

interface ProductData {
  product: ProductListItem[]
  current: number
  pageSize: number
  totalSize: number
}

// 登录接口返回数据结构定义
interface ProductListResultType<T> {
  success: boolean
  state: number
  message: string
  data: T
}

// 查询接口
const productListRequest = (params: ProductListType) => {
  console.info(params)

  return request_handler<ProductListResultType<ProductData>>({
    method: 'POST',
    url: '/products/list',
    data: { current_page: params.currentPage, page_size: params.pageSize }
  })
}

// 查询 - 条件
const queryCondition = ref<ProductListType>({
  currentPage: 1,
  pageSize: 10
} as ProductListType)

// 查询 - 结果
const queriedResult = ref<ProductListResultType<ProductData>>(
  {} as ProductListResultType<ProductData>
)

// 查询 - 方法
const getProductList = async () => {
  // params: ProductListType = {}
  // Object.assign(queryCondition.value, params) // 用于外部灵活使用
  const { data } = await productListRequest(queryCondition.value)
  if (data.state === 0) {
    queriedResult.value = data
  } else {
    ElMessage.error('商品接口错误')
    throw new Error('商品接口错误')
  }
}

export { queryCondition, queriedResult, getProductList }
