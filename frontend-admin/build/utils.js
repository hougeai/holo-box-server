import fs from 'fs'
import path from 'path'
import dotenv from 'dotenv'

/**
 * * 项目根路径
 * @descrition 结尾不带/
 */
export function getRootPath() {
  return path.resolve(process.cwd()) // 返回的就是项目根路径
}

/**
 * * 项目src路径
 * @param srcName src目录名称(默认: "src")
 * @descrition 结尾不带斜杠
 */
export function getSrcPath(srcName = 'src') {
  return path.resolve(getRootPath(), srcName)
}

export function convertEnv(envOptions) {
  const result = {}
  if (!envOptions) return result

  for (const envKey in envOptions) {
    let envVal = envOptions[envKey]
    if (['true', 'false'].includes(envVal)) envVal = envVal === 'true'

    if (['VITE_PORT'].includes(envKey)) envVal = +envVal //将 envVal 从字符串转换为数字

    result[envKey] = envVal
  }
  return result
}

/**
 * 获取当前环境下生效的配置文件名
 */
function getConfFiles() {
  const script = process.env.npm_lifecycle_script // 一个环境变量，包含了当前运行的 npm 脚本的完整命令字符串。
  const reg = new RegExp('--mode ([a-z_\\d]+)') // 在 npm 脚本命令中找到了 --mode 参数
  const result = reg.exec(script)
  if (result) {
    const mode = result[1]
    return ['.env', '.env.local', `.env.${mode}`]
  }
  return ['.env', '.env.local', '.env.production']
}

export function getEnvConfig(match = 'VITE_', confFiles = getConfFiles()) {
  let envConfig = {}
  confFiles.forEach((item) => {
    try {
      if (fs.existsSync(path.resolve(process.cwd(), item))) {
        const env = dotenv.parse(fs.readFileSync(path.resolve(process.cwd(), item)))
        envConfig = { ...envConfig, ...env }
      }
    } catch (e) {
      console.error(`Error in parsing ${item}`, e)
    }
  })
  const reg = new RegExp(`^(${match})`)
  Object.keys(envConfig).forEach((key) => {
    if (!reg.test(key)) {
      Reflect.deleteProperty(envConfig, key)
    }
  })
  return envConfig
}
