<template>
  <div id="map-container"></div>
</template>

<script setup>
import { onMounted, ref, watch } from 'vue';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';
import { antPath } from 'leaflet-ant-path';

// FIX: Manually import and set Leaflet icon images to solve Vite path issues
// This is a common fix for Leaflet in module bundlers.
import iconRetinaUrl from 'leaflet/dist/images/marker-icon-2x.png';
import iconUrl from 'leaflet/dist/images/marker-icon.png';
import shadowUrl from 'leaflet/dist/images/marker-shadow.png';

delete L.Icon.Default.prototype._getIconUrl;

L.Icon.Default.mergeOptions({
  iconRetinaUrl: iconRetinaUrl,
  iconUrl: iconUrl,
  shadowUrl: shadowUrl,
});

const props = defineProps({
  locations: {
    type: Array,
    required: true,
  },
  path: {
    type: Array,
    default: () => [],
  },
});

const emit = defineEmits(['add-location']);
const map = ref(null);
const markersLayer = ref(null);
const pathLayer = ref(null);

onMounted(() => {
  try {
    map.value = L.map('map-container').setView([31.2304, 121.4737], 12);
    
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
    }).addTo(map.value);

    markersLayer.value = L.layerGroup().addTo(map.value);
    pathLayer.value = L.layerGroup().addTo(map.value);

    // 监听地图点击事件
    map.value.on('click', onMapClick);

  } catch (error) {
    console.error("FATAL: Failed to initialize map:", error);
  }
});

const onMapClick = (e) => {
  const latlng = e.latlng;

  // --- 创建弹出窗口内容的容器 ---
  const container = document.createElement('div');

  // --- 创建并填充坐标信息 ---
  const coordsDiv = document.createElement('div');
  coordsDiv.innerHTML = `
    <strong>坐标:</strong><br/>
    纬度: ${latlng.lat.toFixed(5)}<br/>
    经度: ${latlng.lng.toFixed(5)}
  `;

  // --- 以编程方式创建按钮并直接附加事件监听器 ---
  const btn = document.createElement('button');
  btn.innerHTML = '添加到客户点';
  btn.className = 'popup-button'; // 使用 class 而不是 id
  
  // 直接将事件处理函数绑定到按钮上
  btn.onclick = () => {
    emit('add-location', { x: latlng.lng, y: latlng.lat });
    map.value.closePopup();
  };

  // --- 将内容添加到容器 ---
  container.appendChild(coordsDiv);
  container.appendChild(btn);

  // --- 创建并打开弹出窗口 ---
  L.popup()
    .setLatLng(latlng)
    .setContent(container)
    .openOn(map.value);
};

// 绘制地点标记
const updateMarkers = () => {
  if (!markersLayer.value) {
    return;
  }
  markersLayer.value.clearLayers();
  if (props.locations.length > 0) {
    try {
      props.locations.forEach(loc => {
        const marker = L.marker([loc.y, loc.x]).addTo(markersLayer.value);
        marker.bindPopup(`ID: ${loc.id}`);
      });
      // 调整地图视野以包含所有点
      const bounds = L.latLngBounds(props.locations.map(loc => [loc.y, loc.x]));
      map.value.fitBounds(bounds.pad(0.1));
    } catch(error) {
      console.error("ERROR: Failed to update markers:", error);
    }
  }
};

// 绘制路径
const drawPath = () => {
  if (!pathLayer.value) {
    return;
  }
  pathLayer.value.clearLayers();
  if (props.path.length > 1 && props.locations.length > 0) {
    try {
      const locationMap = new Map(props.locations.map(loc => [loc.id, loc]));
      const latLngs = [];
      
      props.path.forEach((id, index) => {
        const loc = locationMap.get(id);
        if (loc) {
          const latLng = [loc.y, loc.x];
          latLngs.push(latLng);

          // 为路径上的点添加序号标记 (跳过起点)
          if (index > 0) {
            const numberIcon = L.divIcon({
              className: 'path-number-icon',
              html: `<span>${index}</span>`,
              iconSize: [24, 24],
              iconAnchor: [12, 12]
            });
            L.marker(latLng, { icon: numberIcon }).addTo(pathLayer.value);
          }
        }
      });

      // 闭合路径
      if (latLngs.length > 0) {
        latLngs.push(latLngs[0]);
      }
      
      // 使用 antPath 替换 polyline
      antPath(latLngs, {
        "delay": 800,
        "dashArray": [10, 20],
        "weight": 5,
        "color": "#0000FF",
        "pulseColor": "#FFFFFF",
        "paused": false,
        "reverse": false,
        "hardwareAccelerated": true
      }).addTo(pathLayer.value);
    } catch(error) {
      console.error("ERROR: Failed to draw path:", error);
    }
  }
};

// 监听locations变化
watch(() => props.locations, updateMarkers, { deep: true, immediate: true });

// 监听path变化
watch(() => props.path, drawPath, { deep: true });

</script>

<style>
/* 将样式移出 scoped，以便能影响到 Leaflet 的原生 popup */
#map-container {
  width: 100%;
  height: 100%;
}
.popup-button {
  margin-top: 10px;
  padding: 5px 10px;
  border: none;
  background-color: #28a745;
  color: white;
  border-radius: 4px;
  cursor: pointer;
}
.path-number-icon {
  background-color: rgba(255, 255, 255, 0.8);
  border: 2px solid #007bff;
  border-radius: 50%;
  display: flex;
  justify-content: center;
  align-items: center;
  font-weight: bold;
  color: #007bff;
}
.popup-button:hover {
  background-color: #218838;
}
</style>