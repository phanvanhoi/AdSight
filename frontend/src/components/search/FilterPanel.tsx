interface Props {
  filters: {
    country: string
    ad_type: string
    sort: string
    min_likes: string
  }
  onChange: (key: string, value: string) => void
}

export default function FilterPanel({ filters, onChange }: Props) {
  return (
    <div className="bg-white rounded-xl border border-gray-200 p-4 space-y-4">
      <h3 className="font-semibold text-gray-900 text-sm">Bo loc</h3>

      {/* Country */}
      <div>
        <label className="text-xs font-medium text-gray-500 uppercase">Quoc gia</label>
        <select
          value={filters.country}
          onChange={(e) => onChange('country', e.target.value)}
          className="mt-1 w-full px-3 py-2 bg-gray-50 border border-gray-200 rounded-lg text-sm"
        >
          <option value="">Tat ca</option>
          <option value="VN">Viet Nam</option>
          <option value="TH">Thai Lan</option>
          <option value="ID">Indonesia</option>
          <option value="PH">Philippines</option>
          <option value="MY">Malaysia</option>
          <option value="SG">Singapore</option>
        </select>
      </div>

      {/* Ad Type */}
      <div>
        <label className="text-xs font-medium text-gray-500 uppercase">Loai ads</label>
        <select
          value={filters.ad_type}
          onChange={(e) => onChange('ad_type', e.target.value)}
          className="mt-1 w-full px-3 py-2 bg-gray-50 border border-gray-200 rounded-lg text-sm"
        >
          <option value="">Tat ca</option>
          <option value="image">Hinh anh</option>
          <option value="video">Video</option>
          <option value="carousel">Carousel</option>
        </select>
      </div>

      {/* Sort */}
      <div>
        <label className="text-xs font-medium text-gray-500 uppercase">Sap xep</label>
        <select
          value={filters.sort}
          onChange={(e) => onChange('sort', e.target.value)}
          className="mt-1 w-full px-3 py-2 bg-gray-50 border border-gray-200 rounded-lg text-sm"
        >
          <option value="relevance">Lien quan nhat</option>
          <option value="newest">Moi nhat</option>
          <option value="engagement">Tuong tac cao</option>
        </select>
      </div>

      {/* Min Likes */}
      <div>
        <label className="text-xs font-medium text-gray-500 uppercase">Likes toi thieu</label>
        <input
          type="number"
          value={filters.min_likes}
          onChange={(e) => onChange('min_likes', e.target.value)}
          placeholder="0"
          className="mt-1 w-full px-3 py-2 bg-gray-50 border border-gray-200 rounded-lg text-sm"
        />
      </div>
    </div>
  )
}
