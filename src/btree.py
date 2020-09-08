
def _get_bbox(vertices):
   left   = min(vertices, key = lambda v: v[0])[0]
   right  = max(vertices, key = lambda v: v[0])[0]
   bottom = min(vertices, key = lambda v: v[1])[1]
   top    = max(vertices, key = lambda v: v[1])[1]
   return (left, right, bottom, top)

def _get_bbox_union(bboxes):
   left   = min(bboxes, key = lambda b: b[0])[0]
   right  = max(bboxes, key = lambda b: b[1])[1]
   bottom = min(bboxes, key = lambda b: b[2])[2]
   top    = max(bboxes, key = lambda b: b[3])[3]
   return (left, right, bottom, top)

def _get_bbox_intersection(bbox1, bbox2):
   left   = max(bbox1[0], bbox2[0])
   right  = min(bbox1[1], bbox2[1])
   bottom = max(bbox1[2], bbox2[2])
   top    = min(bbox1[3], bbox2[3])
   if (left < right) and (bottom < top):
      return (left, right, bottom, top)
   else:
      return (0, 0, 0, 0)

def _get_bbox_area(bbox):
   left, right, bottom, top = bbox
   return ((right - left) * (top - bottom))

def _determine_division_axis_and_index(leaves_sorted):
   best_area  = None
   best_axis  = None
   best_index = None
   # Try both axes. For odd number of leaves, try both groups having one leaf more.
   # Select the division in which the intersection of two groups is the smallest.
   for axis in (0, 1):
      i1 = (len(leaves_sorted[axis]))   // 2
      i2 = (len(leaves_sorted[axis])+1) // 2
      for index in (i1,i2) if (i1 != i2) else (i1,):
         bbox1 = _get_bbox_union([leaf['bbox'] for leaf in leaves_sorted[axis][:index]])
         bbox2 = _get_bbox_union([leaf['bbox'] for leaf in leaves_sorted[axis][index:]])
         area = _get_bbox_area(_get_bbox_intersection(bbox1, bbox2))
         if (best_area is None) or (best_area > area):
            best_area = area
            best_axis = axis
            best_index = index
   return (best_axis, best_index)

def _create_btree_node(leaves_sorted):
   leaves = leaves_sorted[0]
   if len(leaves) > 1:
      axis, index = _determine_division_axis_and_index(leaves_sorted)
      l1 = [None, None]
      l2 = [None, None]
      # Divide leaves into two groups as per the determined axis and index.
      l1[axis] = leaves_sorted[axis][:index]
      l2[axis] = leaves_sorted[axis][index:]
      # For sort order based on the other axis, add special attribute to quickly
      # filter out the redundant leaves. Remove the attribute immediately after.
      for leaf in l1[axis]:
         leaf['[1]'] = True
      l1[axis^1] = [leaf for leaf in leaves_sorted[axis^1] if ('[1]' in leaf)]
      l2[axis^1] = [leaf for leaf in leaves_sorted[axis^1] if ('[1]' not in leaf)]
      for leaf in l1[axis]:
         del leaf['[1]']
      # Create a branch node with two children.
      return {
         'bbox': _get_bbox_union([leaf['bbox'] for leaf in leaves]),
         'kind': 'branch',
         'sub1': _create_btree_node(l1),
         'sub2': _create_btree_node(l2)}
   else:
      return leaves[0]

def create_btree_leaves_from_polygons(polygons, vertices):
   return [{
      'bbox': _get_bbox([vertices[i] for i in poly]),
      'kind': 'polygon',
      'order': poly_ix,
      'value': tuple(poly)
      } for (poly_ix, poly) in enumerate(polygons)]

def create_btree_leaves_from_entities(entities, vertices):
   return [{
      'bbox': _get_bbox([vertices[i] for i in ent[2:]]),
      'kind': ent[0],
      'name': ent[1],
      'value': tuple(ent[2:]) if (len(ent) > 3) else ent[2]
      } for ent in entities]

def create_btree(leaves):
   if len(leaves) > 0:
      leaves_sorted = [leaves[:], leaves[:]]
      leaves_sorted[0].sort(key = lambda leaf: (leaf['bbox'][0] + leaf['bbox'][1]) / 2.0) # (left+right)/2
      leaves_sorted[1].sort(key = lambda leaf: (leaf['bbox'][2] + leaf['bbox'][3]) / 2.0) # (bottom+top)/2
      return _create_btree_node(leaves_sorted)
   else:
      return None

def get_polygons_from_btree(root):
   polygons = []

   def traverse_tree(node):
      if node['kind'] == 'branch':
         traverse_tree(node['sub1'])
         traverse_tree(node['sub2'])
      elif node['kind'] == 'polygon':
         polygons.append(node)

   traverse_tree(root)
   polygons.sort(key = lambda poly: poly['order'])
   return [list(poly['value']) for poly in polygons]

def get_entities_from_btree(root):
   entities = []

   def traverse_tree(node):
      if node['kind'] == 'branch':
         traverse_tree(node['sub1'])
         traverse_tree(node['sub2'])
      elif node['kind'] != 'polygon':
         entities.append(node)

   def get_entity(ent):
      try:
         return [ent['kind'], ent['name']] + list(ent['value'])
      except TypeError:
         return [ent['kind'], ent['name'], ent['value']]

   traverse_tree(root)
   return [get_entity(ent) for ent in entities]
