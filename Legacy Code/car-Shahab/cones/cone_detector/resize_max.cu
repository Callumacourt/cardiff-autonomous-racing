__global__ void threshold(float* dst, int n, float threshold)
{
    int i = blockIdx.x * blockDim.x + threadIdx.x;
    if (i >= n)
        return;
    if (dst[i] < threshold)
        dst[i] = 0.0f;
}

__global__ void write_max(float const* const src, float* dst, int n)
{
    int i = blockIdx.x * blockDim.x + threadIdx.x;
    if (i < n)
        dst[i] = max(dst[i], src[i]);
}

__global__ void resize_nn_write_max(float const* src, float* dst,
                                    int oldh, int oldw, int newh, int neww,
                                    float scale_a, float scale_b)
{
    unsigned int x = blockIdx.x * blockDim.x + threadIdx.x;
    unsigned int y = blockIdx.y * blockDim.y + threadIdx.y;

    if ((x >= neww) || (y >= newh))
        return;

    unsigned int dst_pos = y * neww + x;
    int dst_pitch = neww * newh;

    int pitch = oldh * oldw;

    int tx = ((float)x ) * scale_a;
    int ty = ((float)y ) * scale_b;
    int src_pos = ty * oldw + tx;
    dst[dst_pos] = max(dst[dst_pos], src[src_pos]);
    dst[dst_pos + dst_pitch] = max(dst[dst_pos + dst_pitch], src[src_pos + pitch]);
    dst[dst_pos + 2 * dst_pitch] = max(dst[dst_pos + 2 * dst_pitch], src[src_pos + 2 * pitch]);
}

__global__ void resize_bl_write_max(float const* src, float* dst,
                                    int oldh, int oldw, int newh, int neww,
                                    float scale_a, float scale_b)
{
    unsigned int x = blockIdx.x * blockDim.x + threadIdx.x;
    unsigned int y = blockIdx.y * blockDim.y + threadIdx.y;

    if ((x >= neww) || (y >= newh))
        return;

    unsigned int dst_pos = y * neww + x;
    int dst_pitch = neww * newh;
    float tx = ((float)x + 0.5) * scale_a - 0.5;
    float ty = ((float)y + 0.5) * scale_b - 0.5;

    int txi = int(tx);
    int tyi = int(ty);
    float fx = tx - (float)txi;
    float fy = ty - (float)tyi;

    if (txi < 0)
    {
	txi = 0;
	fx = 0.0f;
    }

    if (txi >= oldw - 1)
    {
	txi = oldw - 1;
	fx = 0.0f;
    }

    if (tyi < 0)
    {
	tyi = 0;
	fy = 0.0f;
    }

    if (tyi >= oldh - 1)
    {
	tyi = oldh - 1;
	fy = 0.0f;
    }

    int posul = tyi * oldw + txi;
    int posur = posul + 1;
    int posdl = posul + oldw;
    int posdr = posdl + 1;

    int pitch = oldh * oldw;
    float c1, c2;
    c1 = src[posul] + (src[posdl] - src[posul]) * fy;
    c2 = src[posur] + (src[posdr] - src[posur]) * fy;
    dst[dst_pos] = max(dst[dst_pos], c1 + (c2 - c1) * fx);

    c1 = src[posul + pitch] + (src[posdl + pitch] - src[posul + pitch]) * fy;
    c2 = src[posur + pitch] + (src[posdr + pitch] - src[posur + pitch]) * fy;
    dst[dst_pos + dst_pitch] = max(dst[dst_pos + dst_pitch], c1 + (c2 - c1) * fx);

    c1 = src[posul + 2 * pitch] + (src[posdl + 2 * pitch] - src[posul + 2 * pitch]) * fy;
    c2 = src[posur + 2 * pitch] + (src[posdr + 2 * pitch] - src[posur + 2 * pitch]) * fy;
    dst[dst_pos + 2 * dst_pitch] = max(dst[dst_pos + 2 * dst_pitch], c1 + (c2 - c1) * fx);
}
