using System.Collections;
using System.Collections.Generic;
using UnityEngine;

public class PointCloudRadar : MonoBehaviour
{
    public float RadarDistance = 20;

    public int RadarNum = 360;

    public float SendTime = 0.5f;

    public Color DrawColor;

    public int RayLineAngle = 360;

    private List<Vector3> points;

    private int RotateNum = 0;

    private PointCloud2Publish pointCloud2Publish;

    private void Start()
    {
        RayLineAngle = 360;
        pointCloud2Publish = this.GetComponent<PointCloud2Publish>();
        points = new List<Vector3>();
        StartCoroutine(StartPointCloudRadar());
    }

    IEnumerator StartPointCloudRadar()
    {
        while (true)
        {
            UpdatePointClound2RadarData();
            yield return new WaitForSeconds(SendTime);
        }
    }

    public void UpdatePointClound2RadarData()
    {
        points.Clear();

        for (int i = 0; i < RadarNum; i++)
        {
            Quaternion pianyi = Quaternion.Euler(0, i * (RayLineAngle / RadarNum), 0);

            Vector3 Normal = pianyi * transform.forward;

            CreatRayAndGetPoint(Normal, i * (RayLineAngle / RadarNum), i, DrawColor);
        }

        pointCloud2Publish.SendMessage_Ros(points);
    }

    public void CreatRayAndGetPoint(Vector3 fx, float angle, int id, Color color)
    {
        RaycastHit raycastHit;
        if (Physics.Raycast(this.transform.localPosition, fx, out raycastHit, RadarDistance))
        {
            //获取信息
            points.Add(raycastHit.point);
        }
        //pointCloud2Publish.SendMessage_Ros(raycastHit.point);
        //发送消息
        //Debug.DrawLine(this.transform.localPosition, raycastHit.point, color);
        Debug.DrawLine(transform.position, new Vector3(transform.position.x + Mathf.Sin(angle * (Mathf.PI / 180)) * RadarDistance, transform.position.y, transform.position.z + Mathf.Cos(angle * (Mathf.PI / 180)) * RadarDistance), color);
    }
}
