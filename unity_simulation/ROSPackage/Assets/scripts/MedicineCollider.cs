using System.Collections;
using System.Collections.Generic;
using UnityEngine;

public class MedicineCollider : MonoBehaviour
{
    private Vector3 StartPos;
    private Quaternion StartRoa;
    // Start is called before the first frame update
    void Start()
    {
        StartPos = transform.position;
        StartRoa = transform.rotation;
    }
    private void OnTriggerEnter(Collider other)
    {
        if (other.transform.tag == "HS")
        {
            transform.position = StartPos;
            transform.rotation = StartRoa;
        }
    }
    
}
